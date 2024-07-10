from aiogram.types import CallbackQuery
from app.database import purchase, var, product
from app.bot.utils import buttons
from aiogram.dispatcher.storage import FSMContext


async def purchase_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state('started')
        
    reply_markup = buttons.InlineKeyboard(
        *[
            {'text': x.get('title'), 'data': f'prod_{x.get("id")}'}
            if x.get('activation')
            else {'text': x.get('title'), 'data': x.get('link')}
            for x in await purchase.get(callback.from_user.id)
        ],
        {'text': await var.get_text('main_menu_button'), 'data': 'main'}
    )

    text = await var.get_var('my_purchase_text', str)
    image = await var.get_var('my_purchase_image', str)
    try:
        await callback.message.delete()
    except:
        pass
    if image:
        await callback.message.answer_photo(photo=image, caption=text, reply_markup=reply_markup)
    else:
        await callback.message.answer(text=text, reply_markup=reply_markup)