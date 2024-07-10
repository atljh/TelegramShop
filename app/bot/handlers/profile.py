from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.storage import FSMContext
from app.database import user, withdraw, var, pyramid
from app.bot.utils.buttons import InlineKeyboard
from app.bot.utils import payment
from app.bot.loader import bot 

from datetime import datetime


async def profile_menu(name, user_id):
    balance = await user.balance(user_id)
    text = await var.get_text("profile")
    text = text.format(
        name=name,
        balance=round(float(balance.get('balance')),4),
        coin_balance=int(balance.get('coin_balance')*100)/100,
        pyramid_balance=int(balance.get('pyramid_balance')*100)/100,
    )
    
    img = await var.get_var("profile_image", str)
    buttons = [
        {'text': await var.get_text('finance_button'), 'data': 'finance'},
        {'text': await var.get_text('referral_button'), 'data': 'referral'},
        {'text': await var.get_text('main_menu_button'), 'data': 'main'},
    ]
    # if user_id in (506563771, 1993309130, 1627976955):
    #     buttons.append({'text': await var.get_text('referral_button'), 'data': 'referral'})
    if img:
        return {
            'caption': text,
            'photo': img,
            'reply_markup': InlineKeyboard(*buttons)
        }
    else:
        return {
            'text': text,
            'reply_markup': InlineKeyboard(*buttons)
        }



async def set_profile(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        pass
    menu = await profile_menu(callback.from_user.full_name, callback.from_user.id)
    if menu.get('photo'):
        await callback.message.answer_photo(**menu)
    else:
        await callback.message.answer(**menu)
    
    await state.set_state('profile')


async def input_exchange_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.delete()
        return
    if amount <= 0:
        await message.delete()
        return
    status = await user.exchange(message.from_user.id, amount)
    if status:
        amount = await user.exchange_to_usd(amount)
        await user.coins_to_reserve(message.from_user.id, amount)
        text = await var.get_text('successful_exchange')
        data = await user.save_exchange(message.from_user.id, amount)
    else:
        text = await var.get_text('unsuccessful_exchange')
    await message.answer(text)
    menu = await profile_menu(message.from_user.full_name, message.from_user.id)
    if menu.get('photo'):
        await message.answer_photo(**menu)
    else:
        await message.answer(**menu)
    
    await state.set_state('profile')


async def input_sell_coins(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.delete()
        return
    if amount <= 0:
        await message.delete()
        return
    status = await user.sell_coins(message.from_user.id, amount)
    if status:
        amount = await user.exchange_to_usd(amount)
        text = await var.get_text('successful_exchange')
        data = await user.save_exchange(message.from_user.id, amount)
    else:
        text = await var.get_text('unsuccessful_exchange')
    await message.answer(text)
    menu = await profile_menu(message.from_user.full_name, message.from_user.id)
    if menu.get('photo'):
        await message.answer_photo(**menu)
    else:
        await message.answer(**menu)
    
    await state.set_state('profile')


async def input_exchange_to_pyramid_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.delete()
        return
    if amount <= 0:
        await message.delete()
        return
    status = await user.exchange_to_pyramid(message.from_user.id, amount)
    if status:
        text = await var.get_text('successful_exchange')
    else:
        text = await var.get_text('unsuccessful_exchange')
    await message.answer(text)
    menu = await profile_menu(message.from_user.full_name, message.from_user.id)
    if menu.get('photo'):
        await message.answer_photo(**menu)
    else:
        await message.answer(**menu)
    
    await state.set_state('profile')


async def input_exchange_from_pyramid_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.delete()
        return
    if amount <= 0:
        await message.delete()
        return
    status = await user.exchange_from_pyramid(message.from_user.id, amount)
    if status:
        text = await var.get_text('successful_exchange')
    else:
        text = await var.get_text('unsuccessful_exchange')
    await message.answer(text)
    menu = await profile_menu(message.from_user.full_name, message.from_user.id)
    if menu.get('photo'):
        await message.answer_photo(**menu)
    else:
        await message.answer(**menu)
    
    await state.set_state('profile')


async def input_refill_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        min_refill_amount = await var.get_var('min_refill_amount', int)
        max_refill_amount = await var.get_var('max_refill_amount', int)
        if amount < min_refill_amount or amount > max_refill_amount:
            await message.delete()
            return 
    except:
        await message.delete()
        return
    
    links = await payment.get_refill_links(message.from_user.id, state, amount)
    buttons = [
        *links,
        {'text': await var.get_text('check_payment_button'), 'data': 'check_payment'},
        {'text': await var.get_text('back_button'), 'data': 'profile'},
        {'text': await var.get_text('main_menu_button'), 'data': 'main'},
    ]
    text = await var.get_text('refill_links')
    image = await var.get_var('refill_links_image', str)
    if image:
        await message.answer_photo(caption=text, photo=image, reply_markup=InlineKeyboard(*buttons))
    else:
        await message.answer(text=text, reply_markup=InlineKeyboard(*buttons))

    await state.set_state('refill')


async def refill_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'profile':
        await callback.message.delete()
        menu = await profile_menu(callback.from_user.full_name, callback.from_user.id)
        if menu.get('photo'):
            await callback.message.answer_photo(**menu)
        else:
            await callback.message.answer(**menu)

        await state.set_state('profile')
        return
    
    if callback.data == 'check_payment':
        data = await state.get_data()
        if await payment.check_payment(callback.from_user.id, data.get('qiwi_id')):
            await state.update_data({'qiwi_id': None})
            callback.data = 'profile'
            await refill_handler(callback, state)
            
        else:
            await callback.answer(await var.get_text('unsuccessful_payment_alert'), show_alert=True)
        return
    
    if callback.data == 'manual_refill_payment':
        reply_markup = InlineKeyboard(
            {'text': await var.get_var('close_button', str), 'data': 'close'}
        )
        text = await var.get_text('manual_payment_text')
        data = await state.get_data()
        text = text.format(price=data.get('price'))
        await callback.message.answer(text, reply_markup=reply_markup)
        await callback.answer()
        return


async def input_refill_pyramid(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        min_refill_amount = await var.get_var('min_refill_amount', int)
        max_refill_amount = await var.get_var('max_refill_amount', int)
        if amount < min_refill_amount or amount > max_refill_amount:
            await message.delete()
            return 
    except:
        await message.delete()
        return
    await user.add_refill_var(message.from_user.id, amount)
    links = await payment.get_refill_links(message.from_user.id, state, amount, pyramid=True)
    buttons = [
        *links,
        {'text': await var.get_text('pay_from_balance_button'), 'data': 'pay_from_balance'},
        {'text': await var.get_text('check_payment_button'), 'data': 'check_payment'},
        {'text': await var.get_text('back_button'), 'data': 'profile'},
        {'text': await var.get_text('main_menu_button'), 'data': 'main'},

    ]
    text = await var.get_text('refill_links')
    image = await var.get_var('refill_links_image', str)
    if image:
        await message.answer_photo(caption=text, photo=image, reply_markup=InlineKeyboard(*buttons))
    else:
        await message.answer(text=text, reply_markup=InlineKeyboard(*buttons))

    await state.set_state('refill_pyramid')


async def refill_pyramid_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'profile':
        await callback.message.delete()
        menu = await profile_menu(callback.from_user.full_name, callback.from_user.id)
        if menu.get('photo'):
            await callback.message.answer_photo(**menu)
        else:
            await callback.message.answer(**menu)

        await state.set_state('profile')
        return
    
    if callback.data == 'pay_from_balance':
        amount = (await user.get_refill_var(callback.from_user.id)).get('amount')
        status = await user.pay_pyramid_from_balance(callback.from_user.id, amount)
        if status:
            text = await var.get_text('successful_exchange')
        else:
            text = await var.get_text('unsuccessful_exchange')
        await callback.message.answer(text)
        menu = await profile_menu(callback.from_user.full_name, callback.from_user.id)
        if menu.get('photo'):
            await callback.message.answer_photo(**menu)
        else:
            await callback.message.answer(**menu)
        await state.set_state('profile')
        return


    if callback.data == 'check_payment':
        data = await state.get_data()
        if await payment.check_payment(callback.from_user.id, data.get('qiwi_id')):
            await state.update_data({'qiwi_id': None})
            callback.data = 'profile'
            await refill_handler(callback, state)
            
        else:
            await callback.answer(await var.get_text('unsuccessful_payment_alert'), show_alert=True)
        return
    
    if callback.data == 'manual_refill_payment':
        reply_markup = InlineKeyboard(
            {'text': await var.get_var('close_button', str), 'data': 'close'}
        )
        text = await var.get_text('manual_payment_text')
        data = await state.get_data()
        text = text.format(price=data.get('price'))
        await callback.message.answer(text, reply_markup=reply_markup)
        await callback.answer()
        return


async def select_withdraw_gateway(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'profile':
        await callback.message.delete()
        menu = await profile_menu(callback.from_user.full_name, callback.from_user.id)
        if menu.get('photo'):
            await callback.message.answer_photo(**menu)
        else:
            await callback.message.answer(**menu)

        await state.set_state('profile')
        return

    if callback.data == 'finance':
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('refill_button'), 'data': 'refill'},
            {'text': await var.get_text('withdraw_button'), 'data': 'withdraw'},
            {'text': await var.get_text('exchange_button'), 'data': 'exchange'},
            {'text': await var.get_text('history_button'), 'data': 'history'},
            {'text': await var.get_text('back_button'), 'data': 'profile'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )

        text = await var.get_text('finance')
        img = await var.get_var('finance_image', str)
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('profile')
        return

    if callback.data not in [x.get('id') for x in await withdraw.get_gateways()]:
        return
    await state.update_data({"withdraw_gateway": callback.data})
    await callback.message.delete()
    text = await var.get_text('input_withdraw_address')
    img = await var.get_var('input_withdraw_address_image', str)
    reply_markup = InlineKeyboard(
        {'text': await var.get_text('back_button'), 'data': 'withdraw'}
    )

    if img:
        await callback.message.answer_photo(caption=text, photo=img, reply_markup=reply_markup)
    else:
        await callback.message.answer(text=text, reply_markup=reply_markup)

    await state.set_state("input_withdraw_address")


async def input_withdraw_address(message: Message, state: FSMContext):
    await state.update_data({'withdraw_address': message.text})
    text = await var.get_text('input_withdraw_amount')
    img = await var.get_var('input_withdraw_amount_image', str)
    reply_markup = InlineKeyboard(
        {'text': await var.get_text('back_button'), 'data': 'withdraw'}
    )
    if img:
        await message.answer_photo(caption=text, photo=img, reply_markup=reply_markup)
    else:
        await message.answer(text=text, reply_markup=reply_markup)

    await state.set_state("input_withdraw_amount")


async def input_withdraw_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        min_withdraw_amount = await var.get_var('min_withdraw_amount', int)
        max_withdraw_amount = await var.get_var('max_withdraw_amount', int)
        if amount < min_withdraw_amount or amount > max_withdraw_amount:
            await message.delete()
            return
        if amount > (await user.balance(message.from_user.id)).get('balance'):
            await message.delete()
            return

    except:
        await message.delete()
        return

    data = await state.get_data()
    if await user.pay_in_shop(message.from_user.id, amount):
        await withdraw.add(message.from_user.id, data.get('withdraw_gateway'), data.get('withdraw_address'), amount)
    
    text = await var.get_text('withdraw_request_done')
    img = await var.get_var('withdraw_request_done_image', str)
    if img:
        await message.answer_photo(caption=text, photo=img)
    else:
        await message.answer(text=text)


    menu = await profile_menu(message.from_user.full_name, message.from_user.id)
    if menu.get('photo'):
        await message.answer_photo(**menu)
    else:
        await message.answer(**menu)

    await state.set_state('profile')


async def profile_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(e)
    if callback.data == 'finance':
        buttons = [
            {'text': await var.get_text('refill_button'), 'data': 'refill'},
        ]

        if (await user.withdraw_available()):
            buttons.insert(1, {'text': await var.get_text('withdraw_button'), 'data': 'withdraw'})
        if (await user.exchange_available()):
            buttons.insert(2, {'text': await var.get_text('exchange_button'), 'data': 'exchange'})
        if (await user.history_available()):
            buttons.insert(3, {'text': await var.get_text('history_button'), 'data': 'history'})

        buttons.append({'text': await var.get_text('back_button'), 'data': 'profile'})
        buttons.append({'text': await var.get_text('main_menu_button'), 'data': 'main'})

        text = await var.get_text('finance')
        img = await var.get_var('finance_image', str)
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=InlineKeyboard(*buttons))
        else:
            await callback.message.answer(text=text, reply_markup=InlineKeyboard(*buttons))
        await state.set_state('profile')
        return

    if callback.data == 'refill':
        text = await var.get_text('select_refill')
        img = await var.get_var('select_refill_img', str)

        buttons = [
            {'text': await var.get_text('select_refill_bot'), 'data': 'refill_bot'},
            {'text': await var.get_text('back_button'), 'data': 'finance'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        ]
        if (await user.pyrtoken_available()):
            buttons.insert(1, {'text': await var.get_text('select_refill_pyramid'), 'data': 'refill_pyramid'})
            
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=InlineKeyboard(*buttons))
        else:
            await callback.message.answer(text=text, reply_markup=InlineKeyboard(*buttons))
        await state.set_state('select_refill')
        return


    if callback.data == 'refill_bot':
        # print(await state.get_data())
        text = await var.get_text('refill')
        img = await var.get_var('refill_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'refill'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},

        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('refill')
        return


    if callback.data == 'refill_pyramid':
        text = await var.get_text('refill_pyramid')
        img = await var.get_var('refill_pyramid_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'refill'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},

        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('refill_pyramid')
        return


    if callback.data == 'withdraw':
        text = await var.get_text('select_withdraw_gateway')
        img = await var.get_var('select_withdraw_gateway_image', str)
        buttons = [
            {'text': x.get('title'), 'data': x.get('id')} for x in await withdraw.get_gateways()
        ]
        buttons.append(
            {'text': await var.get_text('back_button'), 'data': 'finance'},
        )
        buttons.append(
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )

        reply_markup = InlineKeyboard(*buttons)
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)

        await state.set_state('select_withdraw_gateway')
        return

    if callback.data == 'exchange':
        text = await var.get_text('select_exchange')
        img = await var.get_var('exchange_image', str)
        buttons = [

            {'text': await var.get_text('sell_coins_button'), 'data': 'sell_coins'},
            {'text': await var.get_text('pyramid_exchange_button'), 'data': 'exchange_pyramid'},
            {'text': await var.get_text('back_button'), 'data': 'finance'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        ]

        if (await user.coins_available()):
           buttons.insert(0, {'text': await var.get_text('coins_exchange_button'), 'data': 'exchange_coins'})     
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=InlineKeyboard(*buttons))
        else:
            await callback.message.answer(text=text, reply_markup=InlineKeyboard(*buttons))
        await state.set_state('select_exchange')
        return

    if callback.data == 'exchange_coins':
        if not (await user.coins_available()):
            return
            
        exchange_kurs = await user.exchange_to_usd_more(1) # One coin = one rub

        text = await var.get_text('exchange')
        text = text.format(exchange_kurs=exchange_kurs)
        img = await var.get_var('exchange_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'exchange'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('exchange')
        return

    if callback.data == 'sell_coins':
        coin_kurs =  await var.get_var('coin_kurs', float)

        text = await var.get_text('sell_coins')
        text = text.format(coin_kurs=coin_kurs)
        img = await var.get_var('sell_coins_image', str)

        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'exchange'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('sell_coins')
        return

    if callback.data == 'exchange_pyramid':
        text = await var.get_text('exchange_pyramid')
        img = await var.get_var('exchange_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('exchange_to_pyramid_button'), 'data': 'exchange_to_pyramid'},
            {'text': await var.get_text('exchange_from_pyramid_button'), 'data': 'exchange_from_pyramid'},
            {'text': await var.get_text('back_button'), 'data': 'exchange'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},

        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('exchange_pyramid')
        return

    if callback.data == 'exchange_to_pyramid':
        text = await var.get_text('exchange_to_pyramid')
        img = await var.get_var('exchange_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'exchange_pyramid'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},

        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('exchange_to_pyramid')
        return

    if callback.data == 'exchange_from_pyramid':
        text = await var.get_text('exchange_from_pyramid')
        img = await var.get_var('exchange_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'exchange_pyramid'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},

        )
        if img:
            await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('exchange_from_pyramid')
        return

    if callback.data == 'history':
        await user.get_ip(callback.from_user.id)
        telegram_id = callback.from_user.id
        withdraw_requests = await user.get_user_withdraw_requests(telegram_id)
        deposits = await user.get_user_deposits(telegram_id)
        exchanges = await user.get_user_exchanges(telegram_id)
        text = await var.get_text('history')
        img = await var.get_var('history_image', str)
        reply_markup = InlineKeyboard(
            {'text': await var.get_text('back_button'), 'data': 'finance'},
            {'text': await var.get_text('main_menu_button'), 'data': 'main'},
        )
        status = {
            None: 'Не обработан',
            'ok': 'Одобрить',
            'bad': 'Отказать'
        }


        if any([withdraw_requests, deposits, exchanges]): 
            withdraw_text = ''
            deposits_text = ''
            exchanges_text = ''
    
            if withdraw_requests:
                template = await var.get_text('withdraw_requests_history')
                for wt in withdraw_requests:
                    withdraw_text +='\n' + template.format(amount=wt.get('amount'),
                     status=status[wt.get('status')], date=wt.get('created_at').strftime("%d/%m/%y %H:%M"))

            if deposits:
                template = await var.get_text('deposits_history')
                for dp in deposits:
                    deposits_text +='\n' + template.format(amount=dp.get('amount'),
                     payment_gateway=dp.get('payment_gateway_id'), date=dp.get('time').strftime("%d/%m/%y %H:%M")) 

            if exchanges:
                template = await var.get_text('exchanges_history')
                for ex in exchanges:
                    exchanges_text += '\n' + template.format(amount=ex.get('amount'), date=ex.get('time').strftime("%d/%m/%y %H:%M"))
                    

            template = await var.get_text('history')
            text = template.format(withdraw_requests_history=withdraw_text,
                     deposits_history=deposits_text, exchanges_history=exchanges_text)
            if len(text) < 4000:
                await callback.message.answer(text=text, reply_markup=reply_markup)
            else:
                await callback.message.answer(text=text[:4000])
                await callback.message.answer(text=text[4000:], reply_markup=reply_markup)
        else:
            text = 'Истории транзакций пока нет'
            if img:
                await callback.message.answer_photo(photo=img, caption=text, reply_markup=reply_markup)
            else:
                await callback.message.answer(text=text, reply_markup=reply_markup)

        return
