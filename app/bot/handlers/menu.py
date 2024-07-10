from aiogram.types import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from app.database import var
from app.database import user as usr
from app.bot.utils.buttons import InlineKeyboard
from app.bot.loader import bot


async def get_chat_link(callback: CallbackQuery, state: FSMContext):
    image = await var.get_var('get_chat_link_image', str)
    text = await var.get_text('get_chat_link_text')
    button = [
        {'text': await var.get_text('channel_sub_button'), 'data': await var.get_text('channel_link')},
        {'text': await var.get_text('check_sub_button'), 'data': 'check_sub'},
        {'text': await var.get_text('back_button'), 'data': 'main'}
    ]
    try:
        await callback.message.delete()
    except:
        pass
    if image:
        try:
            await callback.message.answer_photo(photo=image, caption=text, reply_markup=InlineKeyboard(*button))
        except Exception as e:
            print(e)
        return
    await callback.message.answer(text=text, reply_markup=InlineKeyboard(*button))

async def useful_services(callback: CallbackQuery, state: FSMContext):
    image = await var.get_var('useful_services_image', str)
    text = await var.get_text('useful_services_text')
    button = [
        {'text': await var.get_text('back_button'), 'data': 'main'}
    ]
    if image:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer_photo(photo=image, caption=text, reply_markup=InlineKeyboard(*button))
        return
    
    await callback.message.edit_text(text=text, reply_markup=InlineKeyboard(*button))


async def check_sub(callback: CallbackQuery, state: FSMContext):
    channel_id = await var.get_var('channel_id', int)
    user = await bot.get_chat_member(channel_id, callback.from_user.id)
    button = InlineKeyboard(
        {'text': await var.get_text('main_menu_button'), 'data': 'main'},
    )
    if user.status != 'left':
        try:
            await callback.message.delete()
        except Exception as e:
            print(e)
        if await usr.is_frod(callback.from_user.id):
            await callback.message.answer((await var.get_text('chat_link_redirect')).format(id=await usr.get_id(callback.from_user.id)), reply_markup=button)
        else:
            await callback.message.answer(await var.get_text('chat_link'), reply_markup=button)
    else:
        await callback.message.answer(await var.get_text('sub_and_check'))  
    
    await callback.answer()

