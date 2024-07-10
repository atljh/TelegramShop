from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from app.database import pyramid, var, user, payment
from app.bot.utils.buttons import InlineKeyboard
from app.bot.loader import bot, dp
from aiogram.utils.exceptions import Throttled


async def generate_queue_info() -> str:
    queue = await pyramid.get_10_firts()
    template = await var.get_text("user_invest_template")
    text = ''
    for j, i in enumerate(queue):
        link = ''
        if i.get('telegram_link'):
            link = f'https://t.me/{i.get("telegram_link")}'
        else:
            link = f'tg://user?id={i.get("telegram_id")}'
        text += template.format(**i, link=link, index=j+1) + '\n'
    
    if not text:
        text = await var.get_text("not_investitions_yet") + '\n'

    return text


async def generate_my_investitions(user_id: int, first=False) -> str:
    queue = await pyramid.get_my_investitions(user_id)
    template = await var.get_text("self_invest_template")
    if first:
        if queue:
            return template.format(**queue[0])
        else:
            return ''

    text = ''
    for i in queue:
        text += template.format(**i) + '\n'

    if not text:
        text = await var.get_text("not_self_investitions_yet") + '\n'

    return text


async def generate_reserve():
    reserve = await pyramid.get_reserve()
    return reserve


async def get_pyramid_info(user_id):
    pyramid_data = await pyramid.pyramid_info()
    investitions = await generate_queue_info()
    my_investitions = await generate_my_investitions(user_id)
    reserve = await generate_reserve()

    text = await var.get_text("pyramid_info")
    text_my_invest = await var.get_text("my_investitions")
    text_my_invest = text_my_invest.format(my_investitions=my_investitions)

    text = text.format(**pyramid_data, investitions=investitions, reserve=round(reserve.get('reserve'), 5))
    image = await var.get_var("pyramid_info_image", str)

    buttons = [
        {'text': await var.get_text('invest_button'), 'data': 'invest'},
        {'text': await var.get_text('refresh_button'), 'data': 'refresh'},
        {'text': await var.get_text('pyramid_history_button'), 'data': 'pyramid_history'},
        {'text': await var.get_text('main_menu_button'), 'data': 'main'}
    ]

    if (await pyramid.topping_available()):
        buttons.insert(1, {'text': await var.get_text('topping_button'), 'data': 'topping'})

    if user_id in (441383243, ):
        buttons.append({'text': ' ', 'data': 'test'})


    return image, text, InlineKeyboard(*buttons), my_investitions


async def pyramid_info(callback: CallbackQuery, state: FSMContext):
    image, text, reply_markup, my_investitions = await get_pyramid_info(callback.from_user.id)
    try:
        await callback.message.delete()
        data = await state.get_data()
        message_to_delete = data.get('message_id')
        await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
    except Exception as e:
        pass
    if image:
        await callback.message.answer_photo(photo=image, caption=text, disable_web_page_preview=True)
        await callback.message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        data = await callback.message.answer(text=text, disable_web_page_preview=True)
        await callback.message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
        await state.update_data({'message_id': data.message_id})
    
    await state.set_state("pyramid_info")


async def pyramid_info_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'invest':
        text = await var.get_text("input_invest_amount")
        balance = await user.balance(callback.from_user.id)
        text = text.format(balance=balance.get('pyramid_balance'))

        image = await var.get_var("input_invest_amount_image", str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'pyramid_info'}
        )
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception as e:
            pass
        if image:
            await callback.message.answer_photo(photo=image, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)

        await state.set_state("input_invest_amount")
        return

    if callback.data == 'topping':
        try:
            await dp.throttle('start', rate=3)
        except Throttled:
            await callback.answer(await var.get_text('stop_spam'))
            return
            # await callback.message.reply(await var.get_text('stop_spam'))
        else:
            text = await var.get_text("input_invest_topping")
            balance = await user.balance(callback.from_user.id)
            invest_info = await generate_my_investitions(callback.from_user.id, first=True)
            
            lost_topping_uses_count = await pyramid.get_max_positions_of_topping(callback.from_user.id)
            auto_topping_status = await pyramid.get_autotopping_status(callback.from_user.id)

            auto_topping_text = await var.get_text('autotopping_enabled') if auto_topping_status else await var.get_text('autotopping_disabled')

            text = text.format(balance=balance.get('coin_balance'), invest_info=invest_info,
            lost_topping_uses_count=lost_topping_uses_count, autotopping_status=auto_topping_text, topping_kurs=await var.get_var("topping_coin", int))

            reply_markup = InlineKeyboard(
                {'text': await var.get_text('autotopping_button'), 'data': 'autotopping'},
                {'text': await var.get_text('back_button'), 'data': 'pyramid_info'}
            )
            image = await var.get_var("input_invest_topping_image", str)
            try:
                await callback.message.delete()
                data = await state.get_data()
                message_to_delete = data.get('message_id')
                await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
            except Exception as e:
                pass
            if image:
                await callback.message.answer_photo(photo=image, caption=text, reply_markup=reply_markup)
            else:
                await callback.message.answer(text=text, reply_markup=reply_markup)

            await state.set_state("input_invest_topping")
            return
        
    if callback.data == 'refresh':
        try:
            await dp.throttle('start', rate=3)
        except Throttled:
            await callback.answer(await var.get_text('stop_spam'))
            return
            # await callback.message.reply(await var.get_text('stop_spam'))
        else:
            await pyramid_info(callback, state)
            await state.set_state("pyramid_info")
            return

    if callback.data == 'pyramid_history':
        try:
            await dp.throttle('start', rate=2)
        except Throttled:
            await callback.answer(await var.get_text('stop_spam'))
            return
            # await callback.message.reply(await var.get_text('stop_spam'))
        else:
            pyramid_payments = await user.get_user_pyramid_payment(callback.from_user.id)
            reply_markup = InlineKeyboard(
                {'text': await var.get_text('back_button'), 'data': 'pyramid_info'},
            )
            pyramid_status = {
                True: 'Выплачено',
                False: 'Ожидается начисление'
            }
            pyramid_text = ''
            if not pyramid_payments:
                pyramid_text = await var.get_text('no_pyramid_history')
                
            template = await var.get_text('pyramid_payments_history')
            for py in pyramid_payments:
                if py.get('time'):
                    date = py.get('time').strftime("%d/%m/%y %H:%M")
                else:
                    date = ''
                pyramid_text += '\n' + template.format(deposit=py.get('initial_deposit'),
                    balance=py.get('balance'), status=pyramid_status[py.get("is_done")], date=date)

            if len(pyramid_text) < 4000:
                await callback.message.answer(text=pyramid_text, reply_markup=reply_markup)
            else:
                await callback.message.answer(text=pyramid_text[:4000])
                await callback.message.answer(text=pyramid_text[4000:], reply_markup=reply_markup)
            return

    if callback.data == 'reserve':
        await pyramid.update_reserve_and_balance()
        return


    if callback.data == 'autotopping':
        await pyramid.check_autotopping()
        await callback.message.delete()
        text = await var.get_text("input_minutes_autotopping")
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('autotopping_stop_button'), 'data': 'stop_autotopping'},
            {'text': await var.get_text('back_button'), 'data': 'topping'}
        )

        await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state("input_minutes_autotopping")
        return


    if callback.data == 'stop_autotopping':
        status = await pyramid.stop_autotopping(callback.from_user.id)
        if status:
            text = await var.get_text("auto_topping_disabled")
        else:
            text = await var.get_text("auto_topping_already_disabled")
        await callback.message.answer(text=text)

        text = await var.get_text("input_invest_topping")
        topping_kurs = await var.get_var("topping_coin", int)

        balance = await user.balance(callback.from_user.id)
        invest_info = await generate_my_investitions(callback.from_user.id, first=True)

        lost_topping_uses_count = await pyramid.get_max_positions_of_topping(callback.from_user.id)
        auto_topping_status = await pyramid.get_autotopping_status(callback.from_user.id)
        auto_topping_text = await var.get_text('autotopping_enabled') if auto_topping_status else await var.get_text('autotopping_disabled')
        text = text.format(balance=balance.get('coin_balance'), invest_info=invest_info,
         lost_topping_uses_count=lost_topping_uses_count, autotopping_status=auto_topping_text, topping_kurs=topping_kurs)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('autotopping_button'), 'data': 'autotopping'},
            {'text': await var.get_text('back_button'), 'data': 'pyramid_info'}
        )
        image = await var.get_var("input_invest_topping_image", str)
        try:
            await callback.message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=message_to_delete)
        except Exception as e:
            pass
        if image:
            await callback.message.answer_photo(photo=image, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)

        await state.set_state("input_invest_topping")
        return


    if callback.data == 'test':
        await callback.message.delete()
        await pyramid.topping(callback.from_user.id, bool(True))
        image, text, reply_markup, my_investitions = await get_pyramid_info(callback.from_user.id)

        if image:
            await callback.message.answer_photo(photo=image, caption=text)
            await callback.message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            await callback.message.answer(text=text)
            await callback.message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)

        await state.set_state("pyramid_info")


async def input_minutes_autotopping(message: Message, state: FSMContext):
    try:
        minutes = int(message.text)
        if minutes <= 0:
            await message.delete()
            return

        status = await pyramid.start_autotopping(message.from_user.id, minutes)
        if not status:
            await message.delete()
            text = await var.get_text("auto_topping_already_enabled")
            await message.answer(text)
            return
            
        text = await var.get_text("auto_topping_enabled")
        await message.answer(text)
        image, text, reply_markup, my_investitions = await get_pyramid_info(message.from_user.id)
        try:
            await message.delete()
            data = await state.get_data()
            message_to_delete = data.get('message_id')
            await bot.delete_message(chat_id=message.from_user.id, message_id=message_to_delete)
        except Exception as e:
            pass
        if image:
            await message.answer_photo(photo=image, caption=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            await message.answer(text=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
        
        await state.set_state("pyramid_info")
        return

    except Exception as e:
        await message.delete()
        pass
        return


async def input_invest_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        min_investition_amount = await var.get_var('min_investition_amount', int)
        max_investition_amount = await var.get_var('max_investition_amount', int)
        if amount < min_investition_amount or amount > max_investition_amount:
            await message.delete()
            return

        if amount > (await user.balance(message.from_user.id)).get('pyramid_balance'):
            await message.delete()
            return
        if await user.pay_in_shop(message.from_user.id, amount, pyramid=True):
            await pyramid.add(message.from_user.id, amount)
        else:
            return
    except ValueError as e:
        try:
            if bool(float(message.text)):
                await message.answer(await var.get_text('only_integer_invest'))
        except Exception as e:
            await message.delete()
            return
        await message.delete()
        return
    except Exception as e:
        print(e)
        await message.delete()
        return
    
    await message.answer(await var.get_text('successful_invest'))

    image, text, reply_markup, my_investitions = await get_pyramid_info(message.from_user.id)

    if image:
        await message.answer_photo(photo=image, caption=text)
        await message.answer(text=my_investitions, reply_markup=reply_markup)

    else:
        await message.answer(text=text)
        await message.answer(text=my_investitions, reply_markup=reply_markup)


    await state.set_state("pyramid_info")


async def input_topping_positions(message: Message, state: FSMContext):
    try:
        await dp.throttle('start', rate=2)
    except Throttled:
        return
    else:
        try:
            positions = int(message.text)
            if positions == 0:
                await message.delete()
                return
                
            if positions < 0:
                await message.delete()
                return
            
            if not await pyramid.check_on_topping(message.from_user.id, positions):
                await message.delete()
                return
            topping_kurs = await var.get_var("topping_coin", int)
            amount = positions * topping_kurs
            if amount > (await user.balance(message.from_user.id)).get('coin_balance'):
                await message.delete()
                return
            
            if not await pyramid.check_topping_limit(message.from_user.id, positions):
                await message.answer(await var.get_text('topping_limit'))
                await message.delete()
                return

            real_position = await pyramid.topping(message.from_user.id, positions)
            await pyramid.add_uses_of_topping(message.from_user.id, real_position)
            await user.pay_by_coins(message.from_user.id, real_position*topping_kurs)

        except Exception as e:
            pass
            await message.delete()
            return
        
        await message.answer(await var.get_text('successful_topping'))

        image, text, reply_markup, my_investitions = await get_pyramid_info(message.from_user.id)

        if image:
            await message.answer_photo(photo=image, caption=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            await message.answer(text=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup, disable_web_page_preview=True)

        await state.set_state("pyramid_info")



async def takemoney(message: Message, state: FSMContext):
    try:
        await dp.throttle('start', rate=2)
    except Throttled:
        return
    else:
        if not (await pyramid.takemoney_available()):
            return
        bet_id = int(message.text[10:])
        bet_user = await pyramid.get_pyramid_user(bet_id)

        if not bet_user == message.from_user.id:
            await message.delete()
            return

        await state.update_data({'takemoney_id': bet_id})
        
        text = await var.get_text('takemoney_text')
        reply_markup = InlineKeyboard(
                {'text': await var.get_text('back_button'), 'data': 'pyramid_info'}
            )
        await message.answer(text=text, reply_markup=reply_markup)
        await state.set_state("input_takemoney")
        return


async def input_takemoney(message: Message, state: FSMContext):
    try:
        await dp.throttle('start', rate=2)
    except Throttled:
        return
    else:
        try:
            amount = float(message.text)
        except ValueError as e:
            await message.delete()
            return

        data = await state.get_data()
        bet = await pyramid.get_pyramid_by_id(int(data.get('takemoney_id')))

        min_take = await var.get_var('takemoney_min_amount', float)
        bet_balance = bet.get('balance')
        bet_id = bet.get('id')

        if not bet_balance >= amount >= min_take:
            await message.delete()
            return
        
        await pyramid.takemoney(message.from_user.id, amount, bet_id)

    
        image, text, reply_markup, my_investitions = await get_pyramid_info(message.from_user.id)

        if image:
            await message.answer_photo(photo=image, caption=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup)
        else:
            await message.answer(text=text)
            await message.answer(text=my_investitions, reply_markup=reply_markup)

        await state.set_state("pyramid_info")
        return
