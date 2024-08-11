import os
import json
import requests
import urllib.parse
from hashlib  import md5
from uuid     import uuid4
from random   import randint
from datetime import datetime, timedelta
import aiohttp
from aiogram.dispatcher.storage import FSMContext

from app.database import payment, user, var

from aiocryptopay import AioCryptoPay, Networks
from app.bot.utils import crypto

async def generate_fowpay_link(user_id: int, price: int, discount: int = 0):
    price -= price * discount / 100
    price = round(price, 2)
    shop_id = os.getenv('fowpay_shop_id')
    secret = os.getenv('fowpay_secret')

    order_id = str(user_id * 1000_000 + randint(100_000, 999_999))
    order_amount = price
    sign = md5(f"{shop_id}:{order_amount}:{secret}:{order_id}".encode()).hexdigest()
    params = {
        'shop': shop_id,
        'amount': f"{order_amount}",
        'order': order_id,
        'sign': sign,
    }
    link = 'https://fowpay.com/pay?' + urllib.parse.urlencode(params)
    return link, price


async def generate_qiwi_link(user_id: int, price: int, discount: int = 0):
    price -= price * discount / 100
    price = round(price, 2)
    price = await user.exchange_from_usd(price)
    qiwi_id = uuid4().hex
    link = ''
    async with aiohttp.ClientSession() as session:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.getenv("qiwi_secret_key")}'
        }

        data = {
            'amount': {
                'currency': 'RUB',
                'value': price
            },
            'expirationDateTime': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            'customFields': {
                'user_id': str(user_id)
            }
        }
        async with session.put(f'https://api.qiwi.com/partner/bill/v1/bills/{qiwi_id}', headers=headers, json=data) as resp:
            data = await resp.json()
            if not data:
                return '', 0, ''
            
            link = data.get('payUrl')

    return link, price, qiwi_id



async def generate_freekassa_link(user_id: int, price: float, discount: int = 0, pyramid = False):
    price -= price * discount / 100
    price = await user.exchange_from_usd(price)
    price = round(price, 2)
    shop_id = int(await var.get_text('freekassa_shop'))
    secret = f"{await var.get_text('freekassa_secret')}"
    order_id = str(user_id * 1000_000 + randint(100_000, 999_999))
    
    sign = md5(f'{shop_id}:{price}:{secret}:RUB:{order_id}'.encode()).hexdigest()
    params = {
        'm': shop_id,
        'oa': str(price),
        'currency': 'RUB',
        'o': order_id,
        's': sign,
        'us_key': str(user_id),
    }
    if pyramid:
        params.update({'us_key1': 'pyramid'})
    link = 'https://pay.freekassa.ru?' + urllib.parse.urlencode(params)
    return link, price


async def generate_cryptocloud_link(user_id: int, price: float, discount: int = 0, pyramid = False):
    price -= price * discount / 100
    price = round(price, 2)
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f"TOKEN {await var.get_text('cryptocloud_secret')}"
        }
        data = {
            'shop_id': f"{await var.get_text('cryptocloud_shop')}",
            'amount': price,
            'order_id': str(user_id),
            'pyramid': 'False'
        }
        async with session.post("https://api.cryptocloud.plus/v1/invoice/create", headers=headers, data=data) as resp:
            data = await resp.json()
            if not data:
                return '', 0, ''
            link = data.get('pay_url')
            invoice_id = data.get('invoice_id')
    
    await payment.add_payment_data(user_id, price, invoice_id, pyramid)    
    return link, invoice_id


async def generate_payok_link(user_id: int, price: float, discount: int = 0, pyramid = False):
    price -= price * discount / 100
    price = await user.exchange_from_usd(price)
    price = round(price, 2)

    shop_id = int(await var.get_text('payok_shop'))
    secret = f"{await var.get_text('payok_secret')}"
    print(await var.get_text('payok_secret'))

    order_id = str(user_id + randint(100_000, 999_999))
    currency = 'RUB'
    desc = price

    string_to_hash = f"{price}|{order_id}|{shop_id}|{currency}|{desc}|{secret}"
    sign = md5(string_to_hash.encode()).hexdigest()

    params = {
        'amount': float(price),
        'payment': order_id,
        'shop': int(shop_id),
        'desc': desc,
        'curncy': currency,
        'sign': sign,
        'custom': user_id
    }

    link = 'https://payok.io/pay?' + urllib.parse.urlencode(params)
    print(link, price)
    return link, price


async def generate_cryptobot_link(user_id: int, price: float, discount: int = 0):
    price -= price * discount / 100
    price = round(price, 2)
    commission_amount = await payment.get_payment_gateway_commission('cryptobot')
    commission = price / 100 * commission_amount
    price = price + commission
    invoice = await crypto.create_invoice(asset='USDT', amount=price, payload=str(user_id))
    await payment.add_cryptobot(invoice.invoice_id, user_id, price)
    return invoice.bot_invoice_url, price


async def generate_p2pkassa_link(user_id: int, price: float, discount: int = 0):
    price -= price * discount / 100
    price = await user.exchange_from_usd(price)
    price = round(price, 2)
    order_id = str(user_id + randint(100_000, 999_999))

    data = {
        'project_id': int(await var.get_text("p2pkassa_shop")),
        'apikey': f'{await var.get_text("p2pkassa_secret")}',
        'order_id': order_id,
        'amount': price,
        'data': json.dumps({'user_id': user_id})
    }
    url = 'https://p2pkassa.online/api/v1/link'
    response = requests.post(url, data=data, verify=True)
    result = response.json()
    print(result)
    await payment.add_p2pkassa(int(result.get('id')), user_id, price)

    return result.get('link'), price


async def qiwi_check(qiwi_id: int, user_id: int):
    async with aiohttp.ClientSession() as session:
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {os.getenv("qiwi_secret_key")}'
        }
        async with session.get(f'https://api.qiwi.com/partner/bill/v1/bills/{qiwi_id}', headers=headers) as resp:
            data = await resp.json()
            if not data:
                return False

            if data.get('status', {}).get('value', '') == 'PAID':
                await payment.add(user_id)
                amount_rub = float(data.get('amount', {}).get('value', 0))
                amount = await user.exchange_to_usd(amount_rub)
                await user.refill(user_id, amount)
                await user.create_deposit(user_id, int(data.get('amount', {}).get('value', 0)), 'qiwi')



async def check_payment(user_id: int, qiwi_id: int, amount: int = None) -> bool:
    if amount:
        data = await user.pay_in_shop(user_id, amount, in_shop=True)
        return data
    else:
        return await payment.check_last(user_id)


async def get_refill_links(user_id: int, state: FSMContext, amount: int, pyramid=False):
    gateways = {'manual': 'manual_refill_payment'}
    for gateway in await payment.get_gateways():
        if gateway.get('id') == 'qiwi':
            qiwi_link, _, qiwi_id = await generate_qiwi_link(user_id, amount)
            await state.update_data({'qiwi_id': qiwi_id})
            gateways.update({'qiwi': qiwi_link})

        elif gateway.get('id') == 'freekassa':
            freekassa_link, _ = await generate_freekassa_link(user_id, amount, pyramid=pyramid)
            gateways.update({'freekassa': freekassa_link})

        elif gateway.get('id') == 'fowpay':
            fowpay_link, _ = await generate_fowpay_link(user_id, amount)
            gateways.update({'fowpay': fowpay_link})

        elif gateway.get('id') == 'cryptocloud':
            try:
                cryptocloud_link, invoice_id = await generate_cryptocloud_link(user_id, amount, pyramid=pyramid)
            except Exception:
                cryptocloud_link = None
                pass
            gateways.update({'cryptocloud': cryptocloud_link})
            
    
        elif gateway.get('id') == 'payok':
            payok_link, _ = await generate_payok_link(user_id, amount)
            gateways.update({'payok': payok_link})

        elif gateway.get('id') == 'cryptobot':
            cryptobot_link, _ = await generate_cryptobot_link(user_id, amount)
            gateways.update({'cryptobot': cryptobot_link})

        elif gateway.get('id') == 'p2pkassa':
            p2pkassa_link, _ = await generate_p2pkassa_link(user_id, amount)
            gateways.update({'p2pkassa': p2pkassa_link})

    button = list()

    for gateway in await payment.get_gateways():
        if gateway.get('id') == 'from_balance':
            continue
        if gateway.get('id') == 'manual':
            manual = {'text': gateway.get('title').format(price=amount), 'data': 'manual_refill_payment'}
            continue
        if amount < 2 and gateway.get('id') == 'cryptocloud':
            continue
        text = gateway.get('title').format(price=amount)
        data = gateways.get(gateway.get('id'))

        button.append(
            {'text': text, 'data': data}
        )
    button.append({'text': manual.get('text'), 'data': 'manual_refill_payment'})

    return button