from asyncpg import Connection
from ._core import connection
from . import var

import os
from time import sleep
import requests
from requests import post
from datetime import datetime, timedelta, date
from threading import Thread


@connection
async def bot_start(referral_telegram_id: str, telegram_id: int, first_name: str, last_name: str, telegram_link: str, from_channel_link: bool = False, is_started: bool = True, conn: Connection = None):    
    if referral_telegram_id.isdigit():
        referral_telegram_id = int(referral_telegram_id)
    else:
        referral_telegram_id = None
    
    q = '''INSERT INTO bot_user(telegram_id, first_name, last_name, telegram_link, 
                        joined_at, status, balance, coin_balance, pyramid_balance, referral_id, second_referral_id,
                        balance_from_referral, balance_from_referral_today,balance_from_sec_referral,balance_from_sec_referral_today, is_special_referral, from_channel_link, is_started)
               VALUES($1, $2, $3, $4, NOW(), 'frod', 0, 0, 0,
                      (select id from bot_user where telegram_id=$5 limit 1), (select referral_id from bot_user where telegram_id=$5 limit 1), 0, 0, 0, 0, False, $6, $7)
            ON CONFLICT(telegram_id) DO UPDATE SET
            is_started = EXCLUDED.is_started'''
    await conn.execute(q, telegram_id, first_name, last_name, telegram_link, referral_telegram_id, from_channel_link, is_started)


@connection
async def get_status(telegram_id: str, conn: Connection) -> bool:
    q = '''SELECT status
           FROM bot_user
           WHERE telegram_id = $1'''
    status = await conn.fetchval(q, telegram_id)
    return status


@connection
async def get_ip(telegram_id: int, conn: Connection):
    q = '''SELECT ip
           FROM bot_user 
           WHERE telegram_id = $1'''
    ip = await conn.fetchval(q, telegram_id)
    print(ip)
    return ip
    
    
@connection
async def get_for_spam(spam_id: int, conn: Connection):
    q = '''SELECT telegram_id
           FROM bot_user
           WHERE telegram_id is not NULL'''
           
    users = [x.get('telegram_id') for x in await conn.fetch(q)]
    q = '''SELECT text, image
           FROM bot_spam
           WHERE id = $1'''
    spam = await conn.fetchrow(q, spam_id)
    q = '''SELECT product.id, product.title, product.is_product
           FROM bot_spam_product AS spam_product
           INNER JOIN bot_product AS product ON product.id = spam_product.product_id
           WHERE spam_product.spam_id = $1
           ORDER BY spam_product.index'''
    products = [dict(x) for x in await conn.fetch(q, spam_id)]

    items = list()
    for i in products:
        id = i.get('id')
        title = i.get('title')

        if i.get('is_product'):
            id = f'buy_{id}'
        items.append(
            {'id': id, 'title': title}
        )

    return {
        'users': users,
        'text': spam.get('text'),
        'image': spam.get('image'),
        'products': items
    }

def send_spam(id):
    sleep(3)
    post(f'http://{os.getenv("web_host", "localhost")}:{os.getenv("web_port", 7000)}/spam', json={'id': id})


@connection
async def check_spam_tasks(conn: Connection):
    q = '''SELECT * FROM bot_spam WHERE status = True'''
    spams = [x for x in await conn.fetch(q)]
    for spam in spams:
        if int(spam.get('day')) == datetime.today().weekday():
            spam_time = datetime.combine(date.min, spam.get('time')) - datetime.min
            time_now = datetime.combine(date.min, datetime.now().time()) - datetime.min
            if time_now + timedelta(hours=2) < spam_time < time_now + timedelta(hours=2, minutes=5):
                print('start spam')
                id = spam.get('id')
                Thread(target=send_spam, args=[id]).start()


@connection
async def set_spam_stat(spam_id: int, received_count: int, conn: Connection):
    q = '''UPDATE bot_spam
           SET received_count = $2
           WHERE id = $1'''
    await conn.execute(q, spam_id, received_count)

@connection
async def add_spam_stat(telegram_id: int, conn: Connection):
    q = '''SELECT id FROM bot_user WHERE telegram_id = $1'''
    user_id = await conn.fetchval(q, telegram_id)
    print(user_id)

    q = '''INSERT INTO bot_spam_status(user_id, date)
           VALUES($1, NOW())
           '''
    await conn.execute(q, user_id)



@connection
async def update_user(data, conn: Connection):
    q = '''SELECT telegram_id, first_name, last_name, telegram_link FROM bot_user WHERE telegram_id = $1'''
    user = await conn.fetchrow(q, data.id)
    new_user = {}
    if not user:
        await bot_start('None', data.id, data.first_name, data.last_name, data.username)
        return
    try:
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        telegram_link = user.get('telegram_link')
    except Exception as e:
        print(e)
    flag = False
    if first_name != data.first_name:
        first_name = data.first_name
        flag = True
    if last_name != data.last_name:
        last_name = data.last_name
        flag = True
    if telegram_link != data.username:
        telegram_link = data.username
        flag = True
    if flag:
        q = ''' UPDATE bot_user
                SET first_name = $2,
                    last_name = $3,
                    telegram_link = $4
                WHERE telegram_id = $1'''
        await conn.execute(q, data.id, first_name, last_name, telegram_link)


@connection
async def check_for_answer(text: str, conn: Connection):
    q = '''SELECT keys, answer FROM bot_autoanswer'''

    data = await conn.fetch(q)
    for field in data:
        keys = field.get('keys').split(', ')
        for key in keys:
            if key in text:
                return field.get('answer')


@connection
async def create_ban_poll(poll_id: str, user_id: int, conn: Connection):
    q = '''INSERT INTO bot_banpoll(poll_id, user_id, for_count)
           VALUES($1, $2, 0)'''
    await conn.execute(q, poll_id, user_id)


@connection
async def poll_for_ban(poll_id: str, inc=1, conn: Connection = None):
    q = '''UPDATE bot_banpoll
           SET for_count = for_count + $2
           WHERE poll_id = $1'''
    
    await conn.execute(q, poll_id, inc)
    
    q = '''SELECT user_id, for_count 
           FROM bot_banpoll
           WHERE poll_id = $1'''

    data = await conn.fetchrow(q, poll_id)
    
    q = '''SELECT value
           FROM bot_var
           WHERE id = $1'''
    ban_rate = await conn.fetchval(q, 'ban_rate')
    ban_rate = 10 if ban_rate is None else int(ban_rate)

    if data.get('for_count') >= ban_rate:
        return data.get('user_id')


@connection
async def set_status(user_id: int, status: str, conn: Connection):
    q = '''UPDATE bot_user
           SET status = $2
           WHERE telegram_id = $1'''
    await conn.execute(q, user_id, status)


@connection
async def is_frod(user_id: int, conn: Connection) -> bool:
    q = '''SELECT 1
           FROM bot_user
           WHERE status = 'frod' AND telegram_id = $1'''
    return bool(await conn.fetchval(q, user_id))


@connection
async def get_id(user_id: int, conn: Connection):
    q = '''SELECT id 
           FROM bot_user
           WHERE telegram_id = $1'''
    return await conn.fetchval(q, user_id)


@connection
async def update_frod(id: int, ip: str, user_agent: str, conn: Connection):
    q = '''UPDATE bot_user
           SET ip = $1,
               user_agent = $2,
               status = 'ok'
           WHERE id = $3 AND status = 'frod' '''
    await conn.execute(q, ip, user_agent, id)


@connection
async def balance(user_id: int, conn: Connection):
    q = '''SELECT balance, coin_balance, pyramid_balance
           FROM bot_user
           WHERE telegram_id = $1'''
    data = await conn.fetchrow(q, user_id)
    if data:
        return dict(data)

    return {"balance": 0, "coin_balance": 0, "pyramid_balance": 0}


@connection
async def exchange(user_id: int, coins: int, conn: Connection):
    balance = await exchange_to_usd(coins)
    q = '''UPDATE bot_user
           SET coin_balance = coin_balance + $2,
               balance = balance - $3
           WHERE telegram_id = $1 AND balance - $3 >= 0
           RETURNING 1'''
    return bool(await conn.fetchval(q, user_id, coins, balance))


@connection
async def sell_coins(user_id: int, coins: int, conn: Connection):
    coin_kurs = await var.get_var('coin_kurs', float)
    balance = coins * coin_kurs
    q = '''UPDATE bot_user
           SET coin_balance = coin_balance - $2,
               balance = balance + $3
           WHERE telegram_id = $1 AND coin_balance - $2 >= 0
           RETURNING 1'''
    return bool(await conn.fetchval(q, user_id, coins, balance))



@connection
async def exchange_to_pyramid(user_id: int, amount: int, conn: Connection):
    coins = amount * 0.1
    pyramid = amount - coins
    coins = amount * 10
    q = '''UPDATE bot_user
           SET coin_balance = coin_balance + $2,
               balance = balance - $4,
               pyramid_balance = pyramid_balance + $3
           WHERE telegram_id = $1 AND balance - $4 >= 0
           RETURNING 1'''
    return bool(await conn.fetchval(q, user_id, coins, pyramid, amount))


@connection
async def exchange_from_pyramid(user_id: int, amount: int, conn: Connection):
    q = '''UPDATE bot_user
           SET balance = balance + $2,
               pyramid_balance = pyramid_balance - $2
           WHERE telegram_id = $1 AND pyramid_balance - $2 >= 0
           RETURNING 1'''
    return bool(await conn.fetchval(q, user_id, amount))


@connection
async def coins_to_reserve(telegram_id: int, amount: int, conn: Connection):
    q = '''SELECT usr.id AS id, usr.is_special_referral AS is_special_referral
           FROM bot_user AS usr
           INNER JOIN bot_user AS ref ON ref.referral_id = usr.id
           WHERE ref.telegram_id = $1'''
    
    resp = await conn.fetchrow(q, telegram_id)
    if resp:
        percent = await var.get_var('coins_to_referral', int)
        to_ref = round(amount * percent / 100, 5)
        reserve = round(amount * 0.6, 5)
        ref_id = resp.get('id')
        if ref_id:
            q = ''' UPDATE bot_user
                    SET balance = balance + $1,
                        balance_from_referral = balance_from_referral + $1,
                        balance_from_referral_today = balance_from_referral_today + $1
                    WHERE id = $2'''
            await conn.execute(q, to_ref, ref_id)
    else:   
        reserve = round(amount * 0.9, 5)
    reserve_update_query = '''UPDATE bot_pyramid_info
                              SET reserve = reserve + $1
                              WHERE id = $2'''
    await conn.execute(reserve_update_query, reserve, 1)

@connection
async def save_exchange(user_id: int, amount: int, conn: Connection):
    q = '''INSERT INTO bot_exchange_history (amount, time, user_id)
           SELECT $2, NOW(), usr.id
           FROM bot_user as usr
           WHERE usr.telegram_id = $1
           RETURNING *
        '''
    res = await conn.fetchrow(q, user_id, amount)
    if res:
        return res
    else:
        raise Exception("Error saving exchange")


@connection
async def refill(user_id: int, amount: int, conn: Connection):
    amont = round(amount, 2)
    q = '''UPDATE bot_user
           SET balance = balance + $2
           WHERE telegram_id = $1'''
    await conn.execute(q, user_id, amount)


@connection
async def refill_pyramid(telegram_id: int, amount: int, payment_gateway = 'freekassa', conn: Connection = None):
    q = 'SELECT percent FROM bot_payment_gateway WHERE id = $1'''

    percent = await conn.fetchrow(q, payment_gateway)

    percent = percent.get('percent')
    coins_perc = round(amount * percent / 100, 2)
    coins = round(amount * percent, 2)
    pyramid = round(amount - coins_perc, 2)

    q = '''UPDATE bot_user
           SET pyramid_balance = pyramid_balance + $2
           WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id, pyramid)

    q = '''UPDATE bot_user
           SET coin_balance = coin_balance + $2
           WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id, coins)


@connection
async def create_deposit(user_id: int, amount: int, gateway: str, conn: Connection):
    q = '''INSERT INTO deposit (user_id, payment_gateway_id, amount, time) 
           SELECT usr.id, pm.id, $2, NOW() 
           FROM bot_user as usr 
           JOIN bot_payment_gateway as pm on pm.id = $3
           WHERE usr.telegram_id = $1'''
    await conn.execute(q, user_id, amount, gateway)


@connection
async def pay_in_shop(user_id: int, amount: int, pyramid: bool = False, in_shop=False, conn: Connection = None) -> bool:
    q = '''UPDATE bot_user
            SET balance = balance - $2
            WHERE telegram_id = $1 AND balance - $2 >= 0
            RETURNING 1'''
    res = bool(await conn.fetchval(q, user_id, amount))
    if in_shop and res:
        q = '''SELECT usr.id AS id, usr.is_special_referral AS is_special_referral
               FROM bot_user AS usr
               INNER JOIN bot_user AS ref ON ref.referral_id = usr.id
               WHERE ref.telegram_id = $1'''
        resp = await conn.fetchrow(q, user_id)
        if not resp:
            return res

        q = '''SELECT usr.id AS id, usr.is_special_referral AS is_special_referral
               FROM bot_user AS usr
               INNER JOIN bot_user AS ref ON ref.second_referral_id = usr.id
               WHERE ref.telegram_id = $1'''
        sec_resp = await conn.fetchrow(q, user_id)

        ref_id = resp.get('id')
        sec_ref_id = resp.get('id')
        is_special_referral = resp.get('is_special_referral')
        percent = 0
        if is_special_referral:
            if pyramid:
                percent = await var.get_var('special_referral_pyramid_percent', int)
            if in_shop:
                percent = await var.get_var('special_referral_refill_percent', int)
        else:
            if pyramid:
                percent = await var.get_var('referral_pyramid_percent', int)
            if in_shop:
                percent = await var.get_var('referral_refill_percent', int)
        if ref_id:
            q = '''UPDATE bot_user
                SET balance = balance + $1,
                    balance_from_referral = balance_from_referral + $1,
                    balance_from_referral_today = balance_from_referral_today + $1
                WHERE id = $2'''
            await conn.execute(q, amount * percent / 100, ref_id)
        if sec_ref_id:
            q = '''UPDATE bot_user
                SET balance = balance + $1,
                    balance_from_sec_referral = balance_from_sec_referral + $1,
                    balance_from_sec_referral_today = balance_from_sec_referral_today + $1
                WHERE id = $2'''
            await conn.execute(q, amount * percent / 100, sec_ref_id)
    return res


@connection
async def withdraw(user_id: int, amount: int, gateway: str, address: str, conn: Connection) -> bool:
    q = '''UPDATE bot_user
           SET balance = balance - $2
           WHERE telegram_id = $1 AND balance - $2 >= 0
           RETURNING 1
           '''
    status = bool(await conn.fetchval(q, user_id, amount))
    if not status:
        return False

    
@connection
async def pay_in_shop_from_balance(user_id: int, amount: int, conn: Connection = None):
    bal = await balance(user_id)
    coins_price = amount / 0.01
    if bal.get('coin_balance') >= coins_price:
        q = '''UPDATE bot_user
               SET coin_balance = coin_balance - $2
               WHERE telegram_id = $1'''
        await conn.execute(q, user_id, coins_price)
        return True
    
    if bal.get('balance') >= amount:
        q = '''UPDATE bot_user
               SET balance = balance - $2
               WHERE telegram_id = $1'''
        await conn.execute(q, user_id, amount)
        q = '''SELECT usr.id AS id,
                    usr.is_special_referral AS is_special_referral
               FROM bot_user AS usr
               INNER JOIN bot_user AS ref ON ref.referral_id = usr.id
               INNER JOIN bot_user AS sec_ref ON sec_ref.second_referral_id = usr.id
               WHERE ref.telegram_id = $1'''
        resp = await conn.fetchrow(q, user_id)

        if not resp:
            return True
        ref_id = resp.get('id')
        is_special_referral = resp.get('is_special_referral')
        percent = 0
        if is_special_referral:
            percent = await var.get_var('special_referral_refill_percent', int)
        else:
            percent = await var.get_var('referral_refill_percent', int)
        if ref_id:
            q = '''UPDATE bot_user
                SET balance = balance + $1,
                    balance_from_referral = balance_from_referral + $1,
                    balance_from_referral_today = balance_from_referral_today + $1
                WHERE id = $2'''
            await conn.execute(q, amount * percent / 100, ref_id)
        return True
    
    return False


@connection
async def pay_by_coins(user_id: int, amount: int, conn: Connection = None):
    bal = await balance(user_id)
    if bal.get('coin_balance') >= amount:
        q = '''UPDATE bot_user
               SET coin_balance = coin_balance - $2
               WHERE telegram_id = $1'''
        await conn.execute(q, user_id, amount)
        return True
    return False
    

@connection
async def get_referral_info(user_id: int, conn: Connection = None):
    q = '''SELECT balance_from_referral, balance_from_referral_today, balance_from_sec_referral, balance_from_sec_referral_today
           FROM bot_user
           WHERE telegram_id = $1'''
    balances = await conn.fetchrow(q, user_id)
    if balances:
        balances = dict(balances)
    else:
        balances = {
            "balance_from_referral": 0,
            "balance_from_referral_today": 0,
            "balance_from_sec_referral": 0,
            "balance_from_sec_referral_today": 0
        }
    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.is_started'''
    first_referral_count = await conn.fetchval(q, user_id) or 0

    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.second_referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.is_started'''
    sec_referral_count = await conn.fetchval(q, user_id) or 0
    
    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.from_channel_link'''
    special_referral_count = await conn.fetchval(q, user_id) or 0

    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.joined_at::date = CURRENT_DATE AND rf.is_started'''
    today_referral_count = await conn.fetchval(q, user_id) or 0

    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.second_referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.joined_at::date = CURRENT_DATE AND rf.is_started'''
    today_sec_referral_count = await conn.fetchval(q, user_id) or 0


    q = '''SELECT COUNT(rf.id)
           FROM bot_user AS usr
           INNER JOIN bot_user AS rf ON rf.referral_id = usr.id
           WHERE usr.telegram_id = $1 AND rf.joined_at::date = CURRENT_DATE AND rf.from_channel_link'''
    today_special_referral_count = await conn.fetchval(q, user_id) or 0

    
    info = {
        **balances,
        "all_referral_count": first_referral_count+sec_referral_count,
        "today_referral_count": today_referral_count+today_sec_referral_count,

        "first_referral_count": first_referral_count,
        "sec_referral_count": sec_referral_count,

        "special_referral_count": special_referral_count,
        "today_special_referral_count": today_special_referral_count
    }
    return info


@connection
async def set_zero_referral_balance_today(conn: Connection):
    q = '''UPDATE bot_user
           SET balance_from_referral_today = 0,
           SET balance_from_sec_referral_today = 0'''
    await conn.execute(q)


@connection
async def get_same_telergam_id(conn: Connection):
    q = '''SELECT u.id
           FROM bot_user AS u
           INNER JOIN bot_user AS s ON s.telegram_id = u.telegram_id AND s.id <> u.id'''
    print(await conn.fetch(q))


@connection
async def set_special_referral(telegram_id: int, conn: Connection):
    q = '''UPDATE bot_user
           SET is_special_referral = True
           WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id)


@connection
async def get_referral_by_link(link: str, conn: Connection):
    q = '''SELECT u.telegram_id
           FROM bot_special_referral AS sr
           INNER JOIN bot_user AS u ON sr.user_id = u.id
           WHERE sr.link LIKE $1 || '%'
           LIMIT 1'''
    return await conn.fetchval(q, link)


@connection
async def is_special_referral(telegram_id: int, conn: Connection):
    q = '''SELECT is_special_referral
           FROM bot_user
           WHERE telegram_id=$1'''
    return await conn.fetchval(q, telegram_id)


@connection
async def get_channel_link_text(channel_link: str, telegram_id: int, conn: Connection):
    """
    Fetch text and image associated with the channel link from a database
    """
    try:
        q = '''SELECT id, text, image, mark_id, (SELECT start_link FROM bot_start_answer WHERE id = start_answer_id), button, button_text FROM auto_accept_application WHERE channel_link LIKE $1'''
        data = await conn.fetchrow(q, channel_link + '%')
        if not data:
            return {}
        mark_id = data.get('mark_id')
        if mark_id:
            q = '''UPDATE bot_user SET mark_id = $1 WHERE telegram_id = $2'''
            await conn.fetchrow(q, mark_id, telegram_id)

        return data or {}
    except Exception as e:
        print(f'Error fetching data from the database: {e}')
        return {}


@connection
async def get_channel_link_button_text(channel_link_id: int, conn: Connection):
    try:
        q = '''SELECT id, button_text FROM auto_accept_application WHERE id = $1'''
        data = await conn.fetchrow(q, channel_link_id)
        return data or {}
    except Exception as e:
        print(f'Error fetching data from the database: {e}')
        return {}


@connection
async def get_user_withdraw_requests(telegram_id: int, conn: Connection):
    """
    Retrieves all the withdraw requests of a user with the given Telegram ID.
    """
    q = '''
        SELECT bot_withdraw_request.amount, bot_withdraw_request.status, bot_withdraw_request.created_at
        FROM bot_withdraw_request 
        INNER JOIN bot_user ON bot_withdraw_request.user_id = bot_user.id
        WHERE bot_user.telegram_id = $1'''
    data = await conn.fetch(q, telegram_id)
    return data


@connection
async def get_user_deposits(telegram_id: int, conn: Connection):
    q = '''
        SELECT deposit.payment_gateway_id, deposit.amount, deposit.time
        FROM deposit 
        INNER JOIN bot_user ON deposit.user_id = bot_user.id
        WHERE bot_user.telegram_id = $1
        '''
    data = await conn.fetch(q, telegram_id)
    return data


@connection
async def get_user_purchases(telegram_id: int, conn: Connection):
    q = '''
        SELECT bot_product.title, bot_product.price, bot_purchase.created_at
        FROM bot_purchase 
        INNER JOIN bot_user ON bot_purchase.user_id = bot_user.id
        INNER JOIN bot_product ON bot_purchase.product_id = bot_product.id
        WHERE bot_user.telegram_id = $1
        '''
    data = await conn.fetch(q, telegram_id)
    return data


@connection
async def get_user_exchanges(telegram_id: int, conn: Connection):
    """
    Get exchange history balance to coins
    """
    q = '''
        SELECT bot_exchange_history.amount, bot_exchange_history.time
        FROM bot_exchange_history
        WHERE bot_exchange_history.user_id = (SELECT id FROM bot_user WHERE telegram_id = $1)
        '''
    data = await conn.fetch(q, telegram_id)
    return data


@connection
async def get_user_pyramid_payment(telegram_id: int, conn: Connection):
    q = '''
        SELECT bot_pyramid_queue.initial_deposit, bot_pyramid_queue.balance, bot_pyramid_queue.is_done, bot_pyramid_queue.time 
        FROM bot_pyramid_queue
        WHERE user_id = (SELECT id FROM bot_user WHERE telegram_id = $1)
        '''
    data = await conn.fetch(q, telegram_id)
    return data


@connection
async def add_refill_var(telegram_id: int, amount: int, conn: Connection):
    q = '''
        INSERT INTO bot_refill_vars(telegram_id, amount) VALUES($1, $2)
        '''
    await conn.execute(q, telegram_id, amount)


@connection
async def get_refill_var(telegram_id: int, conn: Connection):
    q = '''
        SELECT amount FROM bot_refill_vars WHERE telegram_id = $1 ORDER BY -id LIMIT 1
        '''
    data = await conn.fetchrow(q, telegram_id)
    return data


@connection
async def pay_pyramid_from_balance(telegram_id: int, amount: int, conn: Connection):
    coins = amount * 0.1
    pyramid = amount - coins
    q = '''UPDATE bot_user
           SET coin_balance = coin_balance + $2,
               balance = balance - $4,
               pyramid_balance = pyramid_balance + $3
           WHERE telegram_id = $1 AND balance - $4 >= 0
           RETURNING 1'''
    return bool(await conn.fetchval(q, telegram_id, coins, pyramid, amount))


@connection
async def update_currency_exchange(conn: Connection):
    token = os.getenv("exchange_token", "2dc90a360f831349f3ee507d")
    url = f'https://v6.exchangerate-api.com/v6/{token}/latest/USD'
    response = requests.get(url)
    data = response.json()
    rub_rate = data['conversion_rates']['RUB']
    q = '''UPDATE bot_kurs
           SET api_kurs = $1
           WHERE id = $2
        '''
    await conn.execute(q, rub_rate, 4)


@connection
async def get_kurs(conn: Connection):
    q = '''
        SELECT
        (CASE WHEN fixed = TRUE THEN personal_kurs ELSE api_kurs END) AS kurs_value
        FROM
        bot_kurs
        LIMIT 1
        '''
    data = await conn.fetchrow(q)
    kurs = data.get('kurs_value')
    return kurs


async def exchange_to_usd(summ: int):
    kurs = await get_kurs()
    return round(summ / kurs, 2)


async def exchange_to_usd_more(summ: int):
    kurs = await get_kurs()
    return round(summ / kurs, 4)


async def exchange_from_usd(summ: int):
    kurs = await get_kurs()
    return round(summ * kurs, 2)


@connection
async def coins_available(conn: Connection):
    q = '''SELECT coins_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status


@connection
async def withdraw_available(conn: Connection):
    q = '''SELECT withdraw_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def exchange_available(conn: Connection):
    q = '''SELECT exchange_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def history_available(conn: Connection):
    q = '''SELECT history_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def pyrtoken_available(conn: Connection):
    q = '''SELECT buy_pyrtoken_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def enter_chat_by_ip_available(conn: Connection):
    q = '''SELECT enter_chat_by_ip from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status


@connection
async def get_start_answer(start_link: str, conn: Connection):
    q = '''SELECT * from bot_start_answer WHERE start_link = $1'''
    answer = await conn.fetchrow(q, start_link)
    if not answer:
        return None
    answer_id = answer.get('id')
    q = '''SELECT product.id, product.title, product.is_product
       FROM bot_start_answer_product AS start_answer_product
       INNER JOIN bot_product AS product ON product.id = start_answer_product.product_id
       WHERE start_answer_product.start_answer_id = $1'''
    products = [dict(x) for x in await conn.fetch(q, answer_id)]
    items = list()
    for i in products:
        id = i.get('id')
        title = i.get('title')

        if i.get('is_product'):
            id = f'buy_{id}'
        items.append(
            {'id': id, 'title': title}
        )
    return {
        'text': answer.get('text'),
        'image': answer.get('image'),
        'products': items
    }


@connection
async def pay_ref(user_id: int, conn: Connection):
    q = '''SELECT usr.id AS id, usr.is_special_referral AS is_special_referral, usr.telegram_id as telegram_id
            FROM bot_user AS usr
            INNER JOIN bot_user AS ref ON ref.referral_id = usr.id
            WHERE ref.id = $1'''
    resp = await conn.fetchrow(q, user_id)
    if not resp:
        return
    ref_id = resp.get('id')
    is_special_referral = resp.get('is_special_referral')
    percent = 0
    if is_special_referral:
        percent = await var.get_var('special_referral_refill_percent', int)
    else:
        percent = await var.get_var('referral_refill_percent', int)

    q = '''SELECT product.price, purchase.id
        FROM bot_purchase AS purchase
        INNER JOIN bot_product AS product ON product.id = purchase.product_id
        WHERE purchase.user_id = $1 AND purchase.referral_payed = False'''
        
    products = await conn.fetch(q, user_id)
    users_to_send = []
    for product in products:
        users_to_send.append({'ref_id': resp.get('telegram_id'), 'percent': product.get('price') * percent / 100})
        if ref_id:
            q = '''UPDATE bot_user
                SET balance = balance + $1,
                    balance_from_referral = balance_from_referral + $1,
                    balance_from_referral_today = balance_from_referral_today + $1
                WHERE id = $2'''
            await conn.execute(q, product.get('price') * percent / 100, ref_id)
            q = '''UPDATE bot_purchase SET referral_payed = True WHERE id = $1'''
            await conn.execute(q, product.get('id'))
    return users_to_send