import os
import hashlib
from hashlib import md5

from aiohttp import web
from aiohttp.web import Request

from app.database import payment, user
from app.bot.loader import bot 


async def fowpay_payment_callback(request: Request):
    user_id = int(int(request.query.get('ORDER_ID')) / 1000_000)
    sign = md5(f"{request.query.get('SHOP_ID')}:{request.query.get('AMOUNT')}:{os.getenv('fowpay_secret')}:{request.query.get('ORDER_ID')}".encode()).hexdigest()
    if sign != request.query.get('SIGN'):
        print(sign, request.query.get('SIGN'), user_id)
        return web.Response(text='BAD')
    
    amount_rub = float(request.query.get('AMOUNT', 0))
    amount = await user.exchange_to_usd(amount_rub)
    await payment.add(user_id)
    await user.refill(user_id, amount)
    await user.create_deposit(user_id, amount, 'fowpay')

    return web.Response(text='OK')

    
async def freekassa_payment_callback(request: Request):
    amount_rub = float(request.query.get('AMOUNT', 0))
    amount_rub * 1.01504906
    amount = round(await user.exchange_to_usd(amount_rub), 2)
    await payment.add(int(request.query.get('us_key', 0)))
    if request.query.get('us_key1', 0):
        await user.refill_pyramid(int(request.query.get('us_key', 0)), amount, payment_gateway='freekassa')
    else:
        await user.refill(int(request.query.get('us_key', 0)), amount)
    try:
        await user.create_deposit(int(request.query.get('us_key', 0)), amount, 'freekassa')
    except Exception as e:
        print(f'exc {e}')

    return web.Response(text='YES')


async def freekassa_payment_redirect(request: Request):
    bot_user = await bot.get_me()
    bot_link = f'https://t.me/{bot_user.username}?start={id}'
    raise web.HTTPFound(bot_link)


async def cryptocloud_payment_callback(request: Request):
    data = await request.post()
    if data['status'] == 'success':
        invoice_id = data['invoice_id']
        data = await payment.get_payment_data(invoice_id)
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        await payment.add(telegram_id)
        if data.get('pyramid'):
            await user.refill_pyramid(telegram_id, amount, payment_gateway='cryptocloud')
        else:
            await user.refill(telegram_id, amount)
        try:
            await user.create_deposit(telegram_id, amount, 'cryptocloud')
        except Exception as e:
            print(f'exc {e}')
    return web.Response(text='OK')


async def payok_payment_callback(request: Request):
    data = await request.post()
    print(data)
    telegram_id = int(data.get('custom[custom]'))
    amount = float(data.get('profit'))
    amount = round(await user.exchange_to_usd(amount), 2)

    await payment.add(telegram_id)
    await user.refill(telegram_id, amount)
    try:
        await user.create_deposit(telegram_id, amount, 'payok')
    except Exception as e:
        print(f'exc {e}')
    return web.Response(text='OK')


