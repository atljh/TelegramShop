import os
from aiogram.types import Message, CallbackQuery, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from app.database import user, var, pyramid, product, system
from aiogram.dispatcher.storage import FSMContext
from app.bot.utils.buttons import InlineKeyboard
from app.bot.loader import bot, dp
from aiogram.utils.exceptions import Throttled
from app.bot.utils import buttons, payment, api

async def start_menu(user_id):
    text = await var.get_text('start_text')
    
    buttons = [
        {'text': await var.get_text('clicker_button'), 'web_app': 'https://xtether.top/clicker'},
        {'text': await var.get_text('profile_button'), 'data': 'profile'},]

    if (await system.shop_available()):
        buttons.insert(2, {'text': await var.get_text('products_button'), 'data': 'products'},)

    if (await system.chat_available()):
        buttons.insert(1, {'text': await var.get_text('get_chat_link_button'), 'data': 'get_chat_link'},)

    if (await pyramid.pyramid_available()):
        buttons.insert(1, {'text': await var.get_text('investitions_button'), 'data': 'pyramid_info'})

    if (await system.register_storage_available()):
        buttons.insert(0, {'text': await var.get_text('register_for_storage'), 'data': 'register_for_storage'})

    if (await system.games_available()):
        buttons.insert(4, {'text': await var.get_text('game_button'), 'data': 'games'},)

    # if user_id in (1993309130, 5759412217, 1627976955, 1863997693,):
        # buttons.append()

    return {
        'text': text,
        'reply_markup': InlineKeyboard(*buttons)

    }

@dp.throttled(rate=2)
async def start(message: Message, state: FSMContext):
    answer = await user.get_start_answer(message.get_args())
    if answer:
        reply_markup = None
        if answer.get('products'):
            reply_markup = buttons.InlineKeyboard(*[{'text': x.get('title'), 'data': x.get('id')} for x in answer.get('products')])
        await bot.send_photo(message.from_user.id, photo=answer.get('image'), caption=answer.get('text'), reply_markup=reply_markup)
        if reply_markup:
            await dp.current_state(chat=message.from_user.id, user=message.from_user.id).set_state('products')
        return

    else:
        st = await state.get_state()
        if st is None:
            referral_telegram_id = message.get_args()
            telegram_id = message.from_user.id
            first_name = message.from_user.first_name
            last_name = message.from_user.last_name
            telegram_link = message.from_user.username
            
            await user.bot_start(referral_telegram_id, telegram_id, first_name, last_name, telegram_link)
            await message.answer(**await start_menu(message.from_user.id))
            await state.set_state('started')
            return

        data = await message.answer(**await start_menu(message.from_user.id))
        await user.update_user(data['chat'])
        await state.set_state('started')


async def main(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        data = await state.get_data()
        if data.get('message_id'):
            await bot.delete_message(chat_id=callback.from_user.id, message_id=data.get('message_id'))
    except Exception as e:
        print(e)
    data = await callback.message.answer(**await start_menu(callback.from_user.id))
    await user.update_user(data['chat'])
    await state.set_state('started')

    
async def reset(message: Message, state: FSMContext):
    await state.finish()
    await message.answer('reseted!')


async def register_storage_handler(callback: CallbackQuery, state: FSMContext):
    data = await product.get_product_storage()
    if data is None:
        return
    product_id = data.get('id')
    await state.update_data({'product_id': product_id})
    text = data.get('text').format(price=data.get('price'))
    if data.get('price') == 0:
        reply_markup = buttons.InlineKeyboard(
            {'text': await var.get_var('get_button', str), 'data': 'get'},
            {'text': await var.get_var('main_menu_button', str), 'data': 'main'}
        )
    else:
        reply_markup = buttons.InlineKeyboard(
            {'text': await var.get_var('buy_button', str), 'data': 'buy'},
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
    await state.set_state('products')