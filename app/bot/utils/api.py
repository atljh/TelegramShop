import os
import requests
import json
import asyncio

from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update

from app.web.loader import app
from app.database import payment, user, var


def get_var_text_sync(var_id):
    loop = asyncio.new_event_loop()
    text = loop.run_until_complete(var.get_text(var_id))
    loop.close()
    return text

crypto_secret = get_var_text_sync('cryptobot_secret')
crypto = AioCryptoPay(token=f"{crypto_secret}", network=Networks.MAIN_NET)


# async def get_crypto():
#     global crypto 
#     crypto = AioCryptoPay(token=f"{await var.get_text('cryptobot_secret')}", network=Networks.MAIN_NET)
#     return crypto

async def close_session(app) -> None:
    await crypto.close()

@crypto.pay_handler()
async def invoice_paid(update: Update, app) -> None:
    print('cr', update)

async def check_cryptobot():
    invoices = await payment.check_cryptobot()
    for invoice in invoices:
        inv = await crypto.get_invoices(invoice_ids=invoice.get('invoice_id'))
        if inv.status == 'paid':
            print(inv)
            await payment.add(int(inv.payload))
            await user.refill(int(inv.payload), inv.amount)
            try:
                await user.create_deposit(int(inv.payload), inv.amount, 'cryptobot')
            except Exception as e:
                print(f'exc {e}')
            await payment.update_cryptobot(invoice.get('invoice_id'))


async def check_p2pkassa():
    invoices = await payment.check_p2pkassa()
    url = 'https://p2pkassa.online/api/v1/getPayment'

    for inv in invoices:
        data = {
            'project_id': int(await var.get_text("p2pkassa_shop")),
            'apikey': f'{await var.get_text("p2pkassa_token")}',
            'id': inv.get('invoice_id'),
        }
        response = requests.post(url, data=data, verify=True)
        content = response.content.decode('utf-8')

        content = content.replace('"{', '{').replace('}"', '}')
        result = json.loads(content)
        if result.get('status') == 'PAID':
            amount = round(await user.exchange_to_usd(inv.get('amount')), 2)
            await payment.add(int(inv.get('telegram_id')))
            await user.refill(int(inv.get('telegram_id')), amount)
            try:
                await user.create_deposit(int(inv.get('telegram_id')), amount, 'p2pkassa')
            except Exception as e:
                print(f'exc {e}')
            await payment.update_p2pkassa(inv.get('invoice_id'))


def get_access_key(url: str, id: str) -> tuple:
    data = {"id": id}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        data = response.json()
        status = data.get('message')
        if not status:
            if not data.get('context'):
                return False, None
            context = data.get('context')
            return False, context

        key = data.get("access_key")
        if key:
            print("Ключ успешно получен и сохранен:", key)
            return True, key
        else:
            print("Ключ не найден в ответе")
    else:
        print("Произошла ошибка при выполнении запроса")
    
    return False, None

app.on_shutdown.append(close_session)
