from aiohttp.web import Request
from aiohttp import web
from app.database import user, var
from app.bot.loader import bot, dp
from app.bot.utils import buttons
import asyncio
from celery import shared_task
from asyncio import sleep


async def spam(request: Request):
    print('got req')
    data = await request.json()
    id = data.get('id')
    data = await user.get_for_spam(id)

    received_count = 0
    reply_markup = None
    if data.get('products'):
        reply_markup = buttons.InlineKeyboard(*[{'text': x.get('title'), 'data': x.get('id')} for x in data.get('products')])
    for user_id in data.get('users'):
        try:
            await bot.send_photo(user_id, photo=data.get('image'), caption=data.get('text'), reply_markup=reply_markup)
            if reply_markup:
                await dp.current_state(chat=user_id, user=user_id).set_state('products')
            received_count += 1
            await user.set_spam_stat(id, received_count)
            await user.add_spam_stat(user_id)
        except Exception as e:
            print(f"Error sending message to chat ID {user_id}: {e}")
        finally:
            await sleep(0.1)
    print('stop spam')
    return web.Response(text='ok')


async def pay_ref(request: Request):
    data = await request.json()
    id = data.get('id')
    data = await user.pay_ref(id)
    for usr in data:
        text = (await var.get_text('refferal_payed')).format(amount=usr.get('percent'))
        await bot.send_message(usr.get('ref_id'), text=text)
    return web.Response(text='ok')
    