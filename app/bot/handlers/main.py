from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.storage import FSMContext
from app.database import product, var, purchase, promocode
from app.database import payment as payment_db
from app.database import user as user_db
from app.bot.utils import buttons, payment, api
from .start import main
from app.bot.loader import bot 



async def get_payment_links(user_id: int, state: FSMContext, discount=0):
    data = await state.get_data()
    product_id = data.get('product_id')

    data = await product.get(product_id)
    amount = data.get('price')

    gateways = {'manual': 'manual_refill_payment'}
    for gateway in await payment_db.get_gateways():
        if gateway.get('id') == 'qiwi':
            qiwi_link, _, qiwi_id = await payment.generate_qiwi_link(user_id, amount, discount)
            await state.update_data({'qiwi_id': qiwi_id})
            gateways.update({'qiwi': qiwi_link})

        elif gateway.get('id') == 'freekassa':
            freekassa_link, _ = await payment.generate_freekassa_link(user_id, amount, discount)
            gateways.update({'freekassa': freekassa_link})

        elif gateway.get('id') == 'fowpay':
            fowpay_link, _ = await payment.generate_fowpay_link(user_id, amount)
            gateways.update({'fowpay': fowpay_link})

        elif gateway.get('id') == 'cryptocloud':
            try:
                cryptocloud_link, invoice_id = await payment.generate_cryptocloud_link(user_id, amount, discount)
            except Exception:
                cryptocloud_link = None
                pass
            gateways.update({'cryptocloud': cryptocloud_link})
            
        elif gateway.get('id') == 'payok':
            payok_link, _ = await payment.generate_payok_link(user_id, amount, discount)
            gateways.update({'payok': payok_link})

        elif gateway.get('id') == 'cryptobot':
            cryptobot_link, _ = await payment.generate_cryptobot_link(user_id, amount, discount)
            gateways.update({'cryptobot': cryptobot_link})

        elif gateway.get('id') == 'p2pkassa':
            p2pkassa_link, _ = await payment.generate_p2pkassa_link(user_id, amount, discount)
            gateways.update({'p2pkassa': p2pkassa_link})

    await state.update_data({'price': amount})
    button = list()
    
    for gateway in await payment_db.get_gateways():
        if gateway.get('id') == 'manual':
            manual = {'text': gateway.get('title').format(price=amount), 'data': 'manual_payment'}
            continue
        if amount < 2 and gateway.get('id') == 'cryptocloud':
            continue
        if gateway.get('id') == 'from_balance':
            balance = await user_db.balance(user_id)
            balance = max(balance.get('balance'), balance.get('coin_balance'))

            if balance < amount:
                continue
            else:
                button.append(
                    {'text': gateway.get('title'), 'data': 'from_balance'}
                )
            continue

        text = gateway.get('title').format(price=amount)
        data = gateways.get(gateway.get('id'))

        button.append(
            {'text': text, 'data': data}
        )

    button.append({'text': manual.get('text'), 'data': 'manual_payment'})
    return button, amount


async def products_menu(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data
    if product_id.startswith('buy_'):
        product_id = product_id.split('_', maxsplit=1)[1]
        data = await product.get(product_id)
        if data is None:
            return
        await state.update_data({'product_id': product_id})
        text = data.get('text').format(price=data.get('price'))
        if data.get('price') == 0:
            reply_markup = buttons.InlineKeyboard(
                {'text': await var.get_var('get_button', str), 'data': 'get'},
                *([{'text': await var.get_text('back_button'), 'data': await product.get_category(product_id)}] if product_id != 'products' else []),
                {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
            )
        else:
            reply_markup = buttons.InlineKeyboard(
                {'text': await var.get_var('buy_button', str), 'data': 'buy'},
                *([{'text': await var.get_text('back_button'), 'data': await product.get_category(product_id)}] if product_id != 'products' else []),
                {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
            )

        try:
            await callback.message.delete()
        except:
            pass
        if data.get('image'):
            await callback.message.answer_photo(photo=data.get('image'), caption=text, reply_markup=reply_markup)
        else:
            try:
                await callback.message.answer(text=text, reply_markup=reply_markup)
            except Exception as e:
                print(e, product_id)
        return 

    data = await product.get_for_menu(product_id)
    if not data:
        return

    reply_markup = buttons.InlineKeyboard(
        *[
            {'text': x.get('title'), 'data': x.get('id')}
            for x in data.get('items')
        ],
        *([{'text': await var.get_text('back_button'), 'data': await product.get_category(product_id)}] if product_id != 'products' else []),
        *([{'text': await var.get_text('purchases_button'), 'data': 'purchases'}] if product_id == 'products' else []),
        {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
    )

    try:
        await callback.message.delete()
    except:
        pass
    if data.get('image'):
        await callback.message.answer_photo(photo=data.get('image'), caption=data.get('text'), reply_markup=reply_markup)
    else:
        await callback.message.answer(text=data.get('text'), reply_markup=reply_markup)
    
    await state.set_state('products')


async def handle_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')
    data = await product.get(product_id)
    if data is None:
        return
    if callback.data == 'get':
        await purchase.add(callback.from_user.id, product_id)
        reply_markup = buttons.InlineKeyboard(
            {'text': data.get('title'), 'data': data.get('link')}
        )
        text = await var.get_text('order_message')
        await callback.message.answer(text=text, reply_markup=reply_markup)

        # await main(callback, state)
        return

    if callback.data == 'buy':
        button, price = await get_payment_links(callback.from_user.id, state)
        text = data.get('text').format(price=price)
        reply_markup = buttons.InlineKeyboard(
            *button,
            {'text': await var.get_text('check_payment_button'), 'data': 'check_payment'},
            {'text': await var.get_text('promocode_button'), 'data': 'promocode'},
            *([{'text': await var.get_text('back_button'), 'data': await product.get_category(product_id)}] if product_id != 'products' else []),
            {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
        )
        try:
            await callback.message.delete()
        except:
            pass

        if data.get('image'):
            mess = await callback.message.answer_photo(photo=data.get('image'), caption=text, reply_markup=reply_markup)
        else:
            mess = await callback.message.answer(text=text, reply_markup=reply_markup)
        await state.set_state('handle_payment')
        await state.update_data({'message_id': mess.message_id})

        return


async def check_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    st = await payment.check_payment(callback.from_user.id, data.get('price'))
    if st:
        await state.update_data({'qiwi_id': None})
        callback.data = 'get'
        try:
            await callback.message.delete()
        except:
            pass
        await handle_product(callback, state)
    else:
        await callback.answer(await var.get_text('unsuccessful_payment_alert'), show_alert=True)


async def promocode_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state('input_promocode')
    await callback.message.answer(await var.get_text('input_promocode_alert'))


async def input_promocode(message: Message, state: FSMContext):
    promo = message.text.strip()
    await message.delete()
    user_info = await state.get_data()
    product_id = user_info.get('product_id')

    data = await product.get(product_id)
    if data is None:
        return

    resp = await promocode.check(promo)
    await bot.delete_message(chat_id=message.chat.id, message_id=user_info.get('message_id'))
    if resp.get('status'):
        await message.answer(await var.get_text('successful_promocode'))
    else:
        await message.answer(await var.get_text('unsuccessful_promocode'))
    button, price = await get_payment_links(message.from_user.id, state, resp.get('discount'))
    text = data.get('text').format(price=price)
    reply_markup = buttons.InlineKeyboard(
        *button,
        {'text': await var.get_text('check_payment_button'), 'data': 'check_payment'},
        {'text': await var.get_text('promocode_button'), 'data': 'promocode'},
        *([{'text': await var.get_text('back_button'), 'data': await product.get_category(product_id)}] if product_id != 'products' else []),
        {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
    )

    if data.get('image'):
        mess = await message.answer_photo(photo=data.get('image'), caption=text, reply_markup=reply_markup)
    else:
        mess = await message.answer(text=text, reply_markup=reply_markup)
    await state.update_data({'message_id': mess.message_id})

    await state.set_state('handle_payment')


async def manual_payment(callback: CallbackQuery, state: FSMContext):
    reply_markup = buttons.InlineKeyboard(
        {'text': await var.get_var('close_button', str), 'data': 'close'}
    )
    text = await var.get_text('manual_payment_text')
    data = await state.get_data()
    text = text.format(price=data.get('price'))
    await callback.message.answer(text, reply_markup=reply_markup)
    await callback.answer()


async def pay_from_balance(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not await user_db.pay_in_shop_from_balance(callback.from_user.id, data.get('price')):
        await callback.answer(await var.get_text('unsuccessful_exchange'), show_alert=True)
        return

    callback.data = 'get'
    try:
        await callback.message.delete()
    except:
        pass
    await handle_product(callback, state)


async def close(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(e)


async def manual(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data[5:]
    prod = await product.get(product_id)
    
    text = (await var.get_text('bought_product')).format(link=prod.get('link'))
    reply_markup = buttons.InlineKeyboard(
        {'text': 'Активировать', 'data': f'activate_{product_id}'},
        {'text': 'Мануал', 'data': prod.get('manual')},
        {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
    )
    await callback.message.answer(text=text, reply_markup=reply_markup)
    return


async def input_product_id(message: Message, state: FSMContext):
    try:
        id = str(message.text)
    except Exception:
        await message.delete()
        return

    data = await state.get_data()
    product_id = data.get('product_to_activate')
    prod = await product.get(product_id)
    status, r_text = api.get_access_key(prod.get('activation_url'), message.text)
    if not status:
        text = await var.get_text('activate_product_error')
        if r_text:
            text = r_text
    else:
        text = (await var.get_text('access_key')).format(access_key=r_text)
        await purchase.activate(message.from_user.id, product_id)
        await state.update_data({f'{product_id}_key': text})
        await state.set_state('started')
        
    await message.answer(text=text)
    return

async def activate(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data[9:]

    activated = await purchase.is_activated(callback.from_user.id, product_id)
    if activated:
    
        data = await state.get_data()
        access_key = data.get(f'{product_id}_key')
        text = (await var.get_text('activated_product')).format(access_key=access_key)
        await callback.message.answer(text=text)
        await callback.answer(text='')
        return

    await callback.message.answer(text=await var.get_text('input_product_id'))
    await callback.answer(text='')
    await state.set_state('input_product_id')
    await state.update_data({'product_to_activate': product_id})

    return


