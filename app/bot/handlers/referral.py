from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.storage import FSMContext
from app.database import user, var
from app.bot.utils import buttons
from app.bot.loader import bot

async def referral_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state("referral")
    reply_markup = buttons.InlineKeyboard(
        {'text': await var.get_text('reload_button'), 'data': 'reload_referral'},
        {'text': await var.get_text('back_button'), 'data': 'profile'},
        {'text': await var.get_text('main_menu_button'), 'data': 'main'}
    )

    bot_user = await bot.get_me()
    bot_link = f'https://t.me/{bot_user.username}?start={callback.from_user.id}'

    if await user.is_special_referral(callback.from_user.id):
        text = await var.get_text('special_referral_text')
    else:
        text = await var.get_text('referral_text')
    text = text.format(
        **await user.get_referral_info(callback.from_user.id),
        link=bot_link
    )

    image = await var.get_var('referral_image', str)
    try:
        await callback.message.delete()
    except:
        pass
    if image:
        await callback.message.answer_photo(photo=image, caption=text, reply_markup=reply_markup)
    else:
        await callback.message.answer(text=text, reply_markup=reply_markup)


async def set_special_referral(message: Message):
    await user.set_special_referral(message.from_user.id)
    await message.answer('OK')

