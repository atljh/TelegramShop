from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.storage import FSMContext
from app.database import var
from app.database import user, knb
from app.bot.utils.buttons import InlineKeyboard, InlineKeyboardMarkup, InlineKeyboardButton
from app.bot.loader import bot, dp
from aiogram.utils.exceptions import Throttled


import asyncio
import math
import random


async def games_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'games':
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception as e:
            pass
        img = await var.get_var('games_image', str)
        text = await var.get_text('games_text')
        balance = await user.balance(callback.from_user.id)
        text = text.format(
            balance=int(balance.get('balance')*100)/100,
            coin_balance=int(balance.get('coin_balance')*100)/100,
            pyramid_balance=int(balance.get('pyramid_balance')*100)/100
        )
        reply_markup = InlineKeyboard(
                {'text': await var.get_text('knb_button'), 'data': 'knb'},
                # {'text': await var.get_text('coinflip_button'), 'data': 'coinflip'},
                {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)

        await state.set_state('games')
        return
    
    if callback.data == 'knb':
        await generate_knb_menu(callback, state)
        return

    if callback.data == 'coinflip':
        return


async def generate_knb_menu(callback: CallbackQuery, state: FSMContext, delete=True, page=1, show_stat=True):
    if delete:
        try:
            await callback.message.delete()
        except Exception as e:
            pass
    
    img = await var.get_var('knb_img', str)
    text = await var.get_text('knb_statistic')
    win, draw, lose = await knb.user_games_statistic(callback.from_user.id)
    balance = await user.balance(callback.from_user.id)
    text = text.format(
        winning_amount=win,
        losing_amount=lose,
        draw_amount=draw,
        balance=int(balance.get('balance') * 100) / 100,
        coin_balance=int(balance.get('coin_balance') * 100) / 100,
        pyramid_balance=int(balance.get('pyramid_balance') * 100) / 100
    )

    games = [dict(x) for x in await knb.get_active_games()]

    # Paginate games

    page_size = 15  
    num_pages = math.ceil(len(games) / page_size)
    if page < 1:
        page = 1
    if page > num_pages:
        page = 1
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    games_page = games[start_index:end_index]
    
    game_template = await var.get_text('knb_list')
    games_text = ''
    for g in games_page:
        gt = game_template.format(
            link=f'https://t.me/{g.get("telegram_link")}',
            first_name=g.get('first_name'),
            amount=g.get('amount'),
            currency=g.get('currency'),
            users_in_room=await knb.get_users_amount(g.get('id')),
            users_amount=g.get('users_amount'),
            id=g.get('id')
        )
        games_text += gt + '\n'

    if not games_page:
        games_text = await var.get_text('no_knb_games')

    buttons = [
        InlineKeyboardButton(await var.get_text('back_knb'), callback_data=f'knb_page_{page-1}'),
        InlineKeyboardButton(await var.get_text('refresh_knb')+f' {page}/{num_pages}', callback_data='refresh'),
        InlineKeyboardButton(await var.get_text('foward_knb'), callback_data=f'knb_page_{page+1}'),
        InlineKeyboardButton(await var.get_text('create_knb_button'), callback_data='create'),
        InlineKeyboardButton(await var.get_text('generate_knb_button'), callback_data='generate_knb'),
        InlineKeyboardButton(await var.get_text('auto_search_knb'), callback_data='autosearch'),
        InlineKeyboardButton(await var.get_text('knb_history_button'), callback_data='history'),
        InlineKeyboardButton(await var.get_text('back_button'), callback_data='games'),
    ]

    reply_markup = InlineKeyboardMarkup(row_width=3)
    reply_markup.add(*buttons)

    if img:
        if show_stat:
            data = await callback.message.answer_photo(photo=img, caption=text)
        await callback.message.answer(text=games_text, reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        if show_stat:
            data = await callback.message.answer(text=text)
        await callback.message.answer(text=games_text, reply_markup=reply_markup, disable_web_page_preview=True)
        
    if show_stat:
        await state.update_data({'message_id': data.message_id})
    await state.set_state('knb')
    return


async def knb_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await dp.throttle('start', rate=2)
    except Throttled:
        await callback.answer(await var.get_text('stop_spam'))
        return
    if callback.data == 'refresh':
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception as e:
            print(e)
        await generate_knb_menu(callback, state)
        return

    if callback.data == 'create':
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception:
            pass
        text = await var.get_text('knb_choose_currency')
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('knb_$'), 'data': '$'},
            {'text': await var.get_text('knb_coins'), 'data': 'coins'},
            {'text': await var.get_text('back_button'), 'data': 'knb'}

        )
        await state.update_data({'autosearch': False})
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return

    if callback.data == 'autosearch':
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception:
            pass
        text = await var.get_text('knb_choose_currency')
        reply_markup = InlineKeyboard(
            {'text': '$', 'data': '$'},
            {'text': 'coins', 'data': 'coins'},
            {'text': await var.get_text('back_button'), 'data': 'knb'}
        )
        await state.update_data({'autosearch': True})
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return

    if callback.data == 'history':
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception:
            pass

        games = await knb.get_knb_history(callback.from_user.id)
        user_link = await var.get_text('users_knb')
        text = await var.get_text('knb_history')
        knb_result = {
            'win':  'Победа',
            'draw': 'Ничья',
            'lose': 'Проигрыш',
            None: 'Активная'
        }
        history = ''
        for g in games:
            users_in_room = await knb.get_users_in_game(g.get('id'))
            users = ''
            if g.get('result') == 'win':
                win_amount = g.get('win_amount', '')
            else:
                win_amount = ''
            win_currency = g.get('currency') if g.get('result') == 'win' else ''
            for usr in users_in_room:
                link = user_link.format(telegram_link=usr.get('telegram_link'), item='')
                users += link
            gt = text.format(
                id=g.get('id'),
                result=knb_result[g.get('result')],
                users_amount=g.get('users_amount'),
                currency=g.get('currency'),
                amount=g.get('amount'),
                users=users,
                win_amount=win_amount,
                win_currency=win_currency
            )
            history += gt + '\n'

        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'knb'}
        )
        if not history:
            history = await var.get_text('no_knb_games')

        await callback.message.answer(text=history, reply_markup=reply_markup)

        # if len(history) < 4000:
            # await callback.message.answer(text=history, reply_markup=reply_markup)
        # else:
            # await callback.message.answer(text=history[:4000])
            # await callback.message.answer(text=history[4000:], reply_markup=reply_markup)
        return

    if callback.data in ['$', 'coins']:
        cur = callback.data
        try:
            await callback.message.delete()
        except Exception as e:
            pass
        await state.update_data({'cur': f'{cur}'})
        data = await callback.answer(f'{cur}')
        text = await var.get_text('knb_enter_amount')
        buttons = []

        if cur == '$':
            buttons += [
                InlineKeyboardButton('0.05', callback_data='0.05_$'),
                InlineKeyboardButton('0.1', callback_data='0.1_$'),
                InlineKeyboardButton('0.25', callback_data='0.25_$'),
                InlineKeyboardButton('0.5', callback_data='0.5_$'),
                InlineKeyboardButton('1', callback_data='1_$'),
                InlineKeyboardButton('2', callback_data='2_$'),
                InlineKeyboardButton('5', callback_data='5_$'),
                InlineKeyboardButton('10', callback_data='10_$')
            ]
        elif cur == 'coins':
            buttons += [
                InlineKeyboardButton('1', callback_data='1_coin'),
                InlineKeyboardButton('2', callback_data='2_coin'),
                InlineKeyboardButton('5', callback_data='5_coin'),
                InlineKeyboardButton('10', callback_data='10_coin'),
                InlineKeyboardButton('25', callback_data='25_coin'),
                InlineKeyboardButton('100', callback_data='100_coin'),
                InlineKeyboardButton('200', callback_data='200_coin'),
                InlineKeyboardButton('500', callback_data='500_coin'),
            ]


        buttons.append(InlineKeyboardButton(await var.get_text('back_button'), callback_data='knb'))
        reply_markup = InlineKeyboardMarkup(row_width=4)
        reply_markup.add(*buttons)

        data = await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.update_data({'message_id': data.message_id})
        await state.set_state('create_knb')
        return

    if callback.data in ['gen_$', 'gen_coins']:
        cur = callback.data[4:]
        await callback.message.delete()
        await state.update_data({'cur': f'{cur}'})
        text = await var.get_text('knb_choose_users_amount')
        reply_markup = InlineKeyboard(
                {'text': '2', 'data': 'gen_2'},
                {'text': '3', 'data': 'gen_3'},
                {'text': await var.get_text('back_button'), 'data': 'knb'},
            )
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return

    if callback.data in ['gen_2', 'gen_3']:
        await callback.message.delete()
        await state.update_data({'knb_users_amount': int(callback.data[4:])})
        text = await var.get_text('input_knb_bet_amount')
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'knb'},
        )
        await callback.message.answer(text=text)
        await state.set_state('input_knb_bet_amount')
        return

    if callback.data in [
        '0.05_$', '0.1_$', '0.25_$', '0.5_$', '1_$', '2_$', '5_$', '10_$',
        '1_coin', '2_coin', '5_coin', '10_coin', '25_coin', '100_coin', '200_coin', '500_coin']:

        amount = float(callback.data.split('_')[0])
        cur = (await state.get_data()).get('cur')
        
        min_amount = await var.get_var(f'min_amount_knb_{cur}', float)
        max_amount = await var.get_var(f'max_amount_knb_{cur}', float)

        if amount < min_amount or amount > max_amount:
            return


        if cur == '$' and (await user.balance(callback.from_user.id)).get('balance') < amount:
            text = await var.get_text('unsuccessful_exchange')
            await callback.answer('', show_alert=False)
            await callback.message.answer(text=text)
            return

        if cur == 'coins' and (await user.balance(callback.from_user.id)).get('coin_balance') < amount:
            text = await var.get_text('unsuccessful_exchange')
            await callback.answer('', show_alert=False)
            await callback.message.answer(text=text)
            return
        await state.update_data({'knb_amount': amount})
        await callback.message.delete()
        text = await var.get_text('knb_choose_users_amount')
        reply_markup = InlineKeyboard(
                {'text': '2', 'data': '2'},
                {'text': '3', 'data': '3'},
                {'text': await var.get_text('back_button'), 'data': 'knb'},

            )
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return

    if callback.data in ['2', '3']: 
        await callback.message.delete()
        await state.update_data({'knb_users_amount': int(callback.data)})
        text = await var.get_text('knb_choose_item')

        if (await state.get_data()).get('autosearch'):
            data = await state.get_data()
            text = await var.get_text('knb_game_preview')
            text = text.format(
                amount = data.get('knb_amount'),
                currency = data.get('cur'),
                users_amount = data.get('knb_users_amount'),
                item = ''
            )
            reply_markup = InlineKeyboard(
                {'text': await var.get_text('auto_search_knb'), 'data': 'start_autosearch'},
                {'text': await var.get_text('back_button'), 'data': 'knb'}
            )
            await callback.message.answer(text=text, reply_markup=reply_markup)
            return
        
        reply_markup = InlineKeyboard(
            {'text': 'Камень', 'data': 'rock'},
            {'text': 'Ножницы', 'data': 'scissors'},
            {'text': 'Бумага', 'data': 'paper'},
            {'text': await var.get_text('back_button'), 'data': 'knb'}
        )
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return

    if callback.data in ['rock', 'paper', 'scissors']:
        await callback.message.delete()
        await state.update_data({'knb_item': callback.data})
        data = await state.get_data()
        items = {
            'rock': 'Камень',
            'paper': 'Бумага',
            'scissors': 'Ножницы'
        }

        text = await var.get_text('knb_game_preview')
        text = text.format(
            amount = data.get('knb_amount'),
            currency = data.get('cur'),
            users_amount = data.get('knb_users_amount'),
            item = items[callback.data]
        )

        reply_markup = InlineKeyboard(
            {'text': 'Создать игру', 'data': 'save_knb'},
            {'text': 'Назад', 'data': 'knb'},
        )
        await callback.message.answer(text=text, reply_markup=reply_markup)
        return


    if callback.data in ['join_rock', 'join_paper', 'join_scissors']:
        item = callback.data[5:]

        items = {
            'rock': 'Камень',
            'paper': 'Бумага',
            'scissors': 'Ножницы'
        }

        knb_result = {
            'win':  'Победа',
            'draw': 'Ничья',
            'lose': 'Проигрыш',
            None: 'Активная'
        }

        data = await state.get_data()
        g = await knb.get_game(data.get('join_knb_id'))


        if g.get('users_amount') == await knb.get_users_amount(g.get('id')):
            text = await var.get_text('room_filled')
            await callback.message.delete()
            await callback.message.answer(text=text)
            await generate_knb_menu(callback, state, delete=False, show_stat=False)
            return

        if not await knb.pay_for_game(callback.from_user.id, g.get('currency'), g.get('amount')):
            text = await var.get_text('unsuccessful_exchange')
            await callback.message.answer(text=text)
            return
        await knb.join_knb(callback.from_user.id, g.get('id'), g.get('amount'), item)
        
        text_template = await var.get_text('knb_game')
        user_link = await var.get_text('users_knb')

        users_in_room = await knb.get_users_in_game(g.get('id'))
        users = ''
        for usr in users_in_room:
            link = user_link.format(telegram_link=usr.get('telegram_link'), item = await var.get_text('knb_hidden_item'))
            users += link + '\n'
        
        text = text_template.format(
            users = users,
            id = g.get('id'),
            amount = g.get('amount'),
            currency = g.get('currency'),
            users_in_game = await knb.get_users_amount(g.get('id')),
            users_amount = g.get('users_amount'),
            smiles = '',
        )
        reply_markup = InlineKeyboard(
                {'text': await var.get_text('back_button'), 'data': 'knb'}
        )

        try:
            await callback.message.delete_reply_markup()
            await callback.message.edit_text(text=text, reply_markup=reply_markup)
        except Exception as e:
            print(e)
        
        if await knb.get_users_amount(g.get('id')) == g.get('users_amount'):
            smiles = await var.get_text('knb_smiles')
            for i in range(5):
                for s in smiles:
                    new_text = text_template.format(
                        users = users,
                        id = g.get('id'),
                        amount = g.get('amount'),
                        currency = g.get('currency'),
                        users_in_game = await knb.get_users_amount(g.get('id')),
                        users_amount = g.get('users_amount'),
                        smiles = f'{s}',
                    )
                    await asyncio.sleep(0.2)
                    try:
                        await callback.message.edit_text(text=new_text, reply_markup=reply_markup)
                    except Exception as e:
                        print(e)

            # ---- GAME STARTED ----

            winners, draws, losers, win_amount = await knb.start_game(g.get('id'))

            # ---- GAME OVER ----
            users_text = ''
            winners_text = ''
            winners_template = await var.get_text('winners_knb')
            end_game_template = await var.get_text('knb_end_game')
            for usr in winners:
                winner_link = winners_template.format(
                    telegram_link = usr.get('telegram_link'),
                    item = items[usr.get('item')],
                    amount = win_amount,
                    currency = g.get('currency')
                )
                winners_text += winner_link + '\n'

            if not len(winners):
                winners_text = 'Ничья'
            
            for usr in users_in_room:
                link = user_link.format(telegram_link = usr.get('telegram_link'), item = items[usr.get('item')])
                users_text += link + '\n'
            
            new_text = end_game_template.format(
                users = users_text,
                id = g.get('id'),
                amount = g.get('amount'),
                currency = g.get('currency'),
                result = knb_result[await knb.get_game_result(callback.from_user.id, g.get('id'))],
                winners = winners_text
            )
            
            try:
                await callback.message.delete()
                await generate_knb_menu(callback, state, delete=False, show_stat=False)
                await callback.message.answer(text=new_text)
            except Exception as e:
                print(e)


            for usr in users_in_room:
                if not callback.from_user.id == usr.get('telegram_id'):
                    text = end_game_template.format(
                            users = users_text,
                            id = g.get('id'),
                            amount = g.get('amount'),
                            currency = g.get('currency'),
                            result = knb_result[await knb.get_game_result(usr.get('telegram_id'), g.get('id'))],
                            winners = winners_text
                        )
                    await bot.send_message(chat_id=usr.get('telegram_id'), text=text, reply_markup=reply_markup)


        return

    if callback.data == 'save_gen_knb':
        await callback.message.delete()
        data = await state.get_data()
        cur = data.get('cur')
        bet_amount = data.get('bet_amount')
        users_amount = data.get('knb_users_amount')
        amount = data.get('total_amount')
        games_amount = data.get('knb_games_amount')
        
        try:
            if cur == '$' and (await user.balance(callback.from_user.id)).get('balance') < amount:
                text = await var.get_text('unsuccessful_exchange')
                await callback.message.answer(text=text)
                await generate_knb_menu(callback, state, delete=False, show_stat=False)
                return

            if cur == 'coins' and (await user.balance(callback.from_user.id)).get('coin_balance') < amount:
                text = await var.get_text('unsuccessful_exchange')
                await callback.message.answer(text=text)
                await generate_knb_menu(callback, state, delete=False, show_stat=False)
                return
        except Exception as e:
            print(e)
            text = await var.get_text('unsuccessful_exchange')
            await callback.message.answer(text=text)
            await generate_knb_menu(callback, state, delete=False, show_stat=False)
            return

        await knb.pay_for_game(callback.from_user.id, cur, amount)

        items = ['rock', 'paper', 'scissors']
        for _ in range(games_amount):
            item = random.choice(items)
            await knb.save_knb(callback.from_user.id, cur, bet_amount, users_amount, item)

        await generate_knb_menu(callback, state)
        return
    
    if callback.data == 'save_knb':
        await callback.message.delete()
        data = await state.get_data()
        cur, amount, users_amount, item = data.get('cur'), data.get('knb_amount'), data.get('knb_users_amount'), data.get('knb_item')
        try:
            if cur == '$' and (await user.balance(callback.from_user.id)).get('balance') < amount:
                text = await var.get_text('unsuccessful_exchange')
                await callback.message.answer(text=text)
                await generate_knb_menu(callback, state, delete=False, show_stat=False)
                return

            if cur == 'coins' and (await user.balance(callback.from_user.id)).get('coin_balance') < amount:
                text = await var.get_text('unsuccessful_exchange')
                await callback.message.answer(text=text)
                await generate_knb_menu(callback, state, delete=False, show_stat=False)
                return
        except Exception as e:
            print(e)
            text = await var.get_text('unsuccessful_exchange')
            await callback.message.answer(text=text)
            await generate_knb_menu(callback, state, delete=False, show_stat=False)
            return

        await knb.pay_for_game(callback.from_user.id, cur, amount)
        await knb.save_knb(callback.from_user.id, cur, amount, users_amount, item)

        await generate_knb_menu(callback, state)
        return


    if callback.data == 'start_autosearch':
        await callback.message.delete()
        data = await state.get_data()
        cur, amount, users_amount = data.get('cur'), data.get('knb_amount'), data.get('knb_users_amount')
        games = await knb.autosearch(amount, cur, users_amount)
        if not games:
            reply_markup = InlineKeyboard(
                {'text': 'Назад', 'data': 'knb'},
            )
            await callback.message.answer(text = await var.get_text('knb_no_autosearch'), reply_markup=reply_markup)
            return
        
        game_template = await var.get_text('knb_list')
        games_text = ''
        for g in games:
            gt = game_template.format(
                link=f'https://t.me/{g.get("telegram_link")}',
                first_name = g.get('first_name'),
                amount = g.get('amount'),
                currency = g.get('currency'),
                users_in_room = await knb.get_users_amount(g.get('id')),
                users_amount = g.get('users_amount'),
                id=g.get('id')
                )
            games_text += gt + '\n'
        reply_markup = InlineKeyboard(
                {'text': await var.get_text('back_button'), 'data': 'knb'},
            )

        await callback.message.answer(text = games_text, reply_markup=reply_markup)
        return

    if callback.data == 'generate_knb':
        await callback.message.delete()
        text = await var.get_text('input_knb_games_amount')
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'knb'},
        )
        await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('input_knb_games_amount')
        return


    if callback.data.startswith('knb_page_'):
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception as e:
            print(e)

        data = callback.data
        page = int(data.split('_')[2])
        await generate_knb_menu(callback, state, page=page)

    return


async def create_knb(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        cur = (await state.get_data()).get('cur')
        min_amount = await var.get_var(f'min_amount_knb_{cur}', float)
        max_amount = await var.get_var(f'max_amount_knb_{cur}', float)
        if amount < min_amount or amount > max_amount:
            await message.delete()
            return

        if cur == '$' and (await user.balance(message.from_user.id)).get('balance') < amount:
            text = await var.get_text('unsuccessful_exchange')
            await message.delete()
            await message.answer(text=text)
            return

        if cur == 'coins' and (await user.balance(message.from_user.id)).get('coin_balance') < amount:
            text = await var.get_text('unsuccessful_exchange')
            await message.delete()
            await message.answer(text=text)
            return

        await state.update_data({'knb_amount': amount})
    except Exception as e:
        print(e)
    try:
        data = await state.get_data()
        message_to_delete = data.get('message_id')
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_to_delete)
    except Exception as e:
        print(e)
    text = await var.get_text('knb_choose_users_amount')
    reply_markup = InlineKeyboard(
            {'text': '2', 'data': '2'},
            {'text': '3', 'data': '3'},
            {'text': await var.get_text('back_button'), 'data': 'knb'},

        )
    await message.answer(text=text, reply_markup=reply_markup)
    return


async def input_knb_games_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1:
            await message.delete()
            return
    except Exception as e:
        await message.delete()
        return

    await state.update_data({'knb_games_amount': amount})

    text = await var.get_text('knb_choose_currency')
    reply_markup = InlineKeyboard(
        {'text': await var.get_text('knb_$'), 'data': 'gen_$'},
        {'text': await var.get_text('knb_coins'), 'data': 'gen_coins'},
        {'text': await var.get_text('back_button'), 'data': 'knb'}
    )
    await message.answer(text=text, reply_markup=reply_markup)
    await state.set_state('knb')
    return


async def input_knb_bet_amount(message: Message, state: FSMContext):
    try:
        bet_amount = float(message.text)
        cur = (await state.get_data()).get('cur')
        min_amount = await var.get_var(f'min_amount_knb_{cur}', float)
        max_amount = await var.get_var(f'max_amount_knb_{cur}', float)
        if bet_amount < min_amount or bet_amount > max_amount:
            await message.delete()
            return
    except Exception as e:
        await message.delete()
        return
    data = await state.get_data()
    games_amount = data.get('knb_games_amount')
    users_amount = data.get('knb_users_amount')
    amount = games_amount * bet_amount
    await state.update_data({'bet_amount': bet_amount, 'total_amount': amount})

    if cur == '$' and (await user.balance(message.from_user.id)).get('balance') < amount:
        text = await var.get_text('unsuccessful_exchange')
        await message.delete()
        await message.answer(text=text)
        return

    if cur == 'coins' and (await user.balance(message.from_user.id)).get('coin_balance') < amount:
        text = await var.get_text('unsuccessful_exchange')
        await message.delete()
        await message.answer(text=text)
        return

    text = await var.get_text('knb_gen_preview')
    text = text.format(
        amount = bet_amount,
        currency = cur,
        games_amount = games_amount,
        users_amount = users_amount,
    )
    reply_markup = InlineKeyboard(
            {'text': await var.get_text('save_gen_knb'), 'data': 'save_gen_knb'},
            {'text': await var.get_text('back_button'), 'data': 'knb'},
        )
    await message.answer(text=text, reply_markup=reply_markup)
    await state.set_state('knb')
    return



async def join_knb(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        message_to_delete = data.get('message_id')
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_to_delete)
    except Exception as e:
        print(e)
    g = await knb.get_game(int(message.text[9:]))
    if g.get('users_amount') == await knb.get_users_amount(g.get('id')):
        text = await var.get_text('room_filled')
        await message.answer(text=text)
        return

    if await knb.check_user_in_game(message.from_user.id, g.get('id')):
        text = await var.get_text('already_in_game_knb')
        await message.answer(text=text)
        return

    if g.get('currency') == '$' and (await user.balance(message.from_user.id)).get('balance') < g.get('amount'):
        text = await var.get_text('unsuccessful_exchange')
        await message.answer(text=text)
        return

    if g.get('currency') == 'coins' and (await user.balance(message.from_user.id)).get('coin_balance') < g.get('amount'):
        text = await var.get_text('unsuccessful_exchange')
        await message.answer(text=text)
        return


    text = await var.get_text('knb_game')
    user_link = await var.get_text('users_knb')
    users_in_room = await knb.get_users_in_game(g.get('id'))
    users = ''
    for usr in users_in_room:
        link = user_link.format(telegram_link=usr.get('telegram_link'), item = await var.get_text('knb_hidden_item'), amount = '')
        users += link + '\n'

    text = text.format(
        users = users,
        id = g.get('id'),
        amount = g.get('amount'),
        currency = g.get('currency'),
        users_in_game = await knb.get_users_amount(g.get('id')),
        users_amount = g.get('users_amount'),
        smiles = '',
        winners = ''
    )

    reply_markup = InlineKeyboard(
            {'text': 'Камень', 'data': 'join_rock'},
            {'text': 'Ножницы', 'data': 'join_scissors'},
            {'text': 'Бумага', 'data': 'join_paper'},
            {'text': await var.get_text('back_button'), 'data': 'knb'},
        )
    await state.update_data({'join_knb_id': g.get('id')})
    await message.answer(text=text, reply_markup=reply_markup)
    return