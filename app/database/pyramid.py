from asyncpg import Connection
from ._core import connection
from app.bot.loader import bot 
from app.database import var, user

from typing import List
import asyncio
from datetime import datetime, timedelta, date
import random


@connection
async def add(telegram_id: int, amount: int, conn: Connection = None):
    index = await conn.fetchval('select MAX(index) from bot_pyramid_queue where not is_done')
    if index == None:
        index = 0
    else:
        index += 1

    bonus = await calculate_bonus(amount)

    q = '''INSERT INTO bot_pyramid_queue(index, balance, max_balance, user_id, is_done, initial_deposit, time, taken)
           VALUES($3, 0, $1,
                  (select id from bot_user where telegram_id = $2),
                  False, $4, NOW(), 0)'''
    await conn.execute(q, bonus, telegram_id, index, amount)
    await evaluate(amount, index, conn)
    await to_bonuses(telegram_id, amount) # To referral and bonuses
    await update_system_fee()
    await regulate_indexes()


async def calculate_bonus(deposit):
    if 1 <= deposit <= 9:
        bonus = 0.10 * deposit
    elif 10 <= deposit <= 49:
        bonus = 0.10 * deposit
    elif 50 <= deposit <= 99:
        bonus = 0.15 * deposit
    elif 100 <= deposit <= 249:
        bonus = 0.20 * deposit
    elif 250 <= deposit <= 499:
        bonus = 0.25 * deposit
    elif deposit >= 500:
        bonus = 0.30 * deposit
    else:
        bonus = 0
    
    total_amount = deposit + bonus
    return total_amount


@connection
async def update_total_plus(amount: float, conn: Connection):
    q = '''UPDATE bot_pyramid_info SET total_plus = total_plus + $1'''
    await conn.execute(q, amount)


@connection
async def topping(telegram_id: int, positions: int, conn: Connection = None):
    q = '''SELECT index FROM bot_pyramid_queue WHERE user_id = (select id from bot_user where telegram_id = $1 limit 1) AND not is_done ORDER BY INDEX LIMIT 1'''
    position_now = await conn.fetchval(q, telegram_id)
    min_position = await conn.fetchval('select min(index) from bot_pyramid_queue where not is_done')
    new_position = position_now - positions
    if new_position < min_position:
        new_position = min_position 
    q = '''UPDATE bot_pyramid_queue
           SET index = index + 1
           WHERE index < $1 AND index >= $2 AND NOT is_done'''  
    await conn.execute(q, position_now, new_position)
    q = '''UPDATE bot_pyramid_queue
           SET index = $2
           WHERE id = (
            select id
            from bot_pyramid_queue
            where user_id = (select id from bot_user where telegram_id = $1 limit 1) and not is_done
            order by index
            limit 1
           )'''
    await conn.execute(q, telegram_id, new_position)
    await regulate_indexes()
    return position_now - new_position


@connection
async def check_topping_limit(telegram_id: int, positions: int, conn: Connection):
    await regulate_indexes()
    q = ''' SELECT (index + 1 - (select min(index) from bot_pyramid_queue where not is_done)) AS index
            FROM bot_pyramid_queue
            WHERE user_id = (select id from bot_user where telegram_id = $1 limit 1)
            AND not is_done
            ORDER BY INDEX
            LIMIT 1'''
    position_now = await conn.fetchval(q, telegram_id)
    new_position = position_now - positions
    if new_position <= 3:
        return False
    if new_position<= 3:
        print(new_position, position_now, positions, telegram_id)
    return True


@connection
async def test_top(conn: Connection):
    q = ''' SELECT (index + 1 - (select min(index) from bot_pyramid_queue where not is_done)) AS index
        FROM bot_pyramid_queue
        WHERE user_id = (select id from bot_user where telegram_id = $1 limit 1)
        AND not is_done
        ORDER BY INDEX
        LIMIT 1'''
    position_now = await conn.fetchval(q, 441383243)
    print(position_now)
    if position_now > 4:
        await topping(441383243, 1)
        

async def evaluate(amount: float, from_index: int, conn: Connection = None):
    q = '''SELECT pq.id, pq.balance, pq.max_balance, pq.initial_deposit, pq.taken, usr.id AS user_id, usr.telegram_link as username, usr.first_name AS user_name, usr.telegram_id AS telegram_id
           FROM bot_pyramid_queue as pq
           INNER JOIN bot_user AS usr ON pq.user_id = usr.id
           WHERE NOT is_done AND index < $1
           ORDER BY index'''

    deposit_message = await var.get_text('deposit_message')
    deposit_direct_message = await var.get_text('deposit_direct_message')
    chat_id = await var.get_var('chat_id', int)

    prc = [0.01, 0.01, 0.01, 0.01, 0.01]
    queue = [dict(x) for x in await conn.fetch(q, from_index)]
    new_queue = list()
    unused = 0
    flag = False
    for user in queue:
        if not prc:
            break
        p = prc.pop(0)
        to_add = user.get('max_balance') - user.get('balance') + user.get('taken')
        summ = float(amount * p)
        if to_add > summ:
            user['balance'] += summ
            user['is_done'] = False
            user['amount'] = summ
            new_queue.append(user)

            await bot.send_message(chat_id=user['telegram_id'], text=deposit_direct_message.format(amount=summ))   
            await bot.send_message(chat_id=chat_id, text=deposit_message.format(username=user.get('username'),user_name=user.get('user_name'), amount=summ), disable_web_page_preview=True)   


        else:
            user['balance'] += to_add
            user['is_done'] = True
            user['amount'] = to_add
            # await update_total_plus(await calculate_bonus(user['initial_deposit']))
            unused += summ - to_add
            new_queue.append(user)

            await bot.send_message(chat_id=user['telegram_id'], text=deposit_direct_message.format(amount=to_add))   
            await bot.send_message(chat_id=chat_id, text=deposit_message.format(username=user.get('username'),user_name=user.get('user_name'), amount=to_add), disable_web_page_preview=True)   


        
    if unused > 0:
        await set_reserve(unused)
    
    data_to_update = [(x.get('id'), x.get('balance'), x.get('is_done')) for x in new_queue]
    q = '''UPDATE bot_pyramid_queue
           SET balance = $2,
               is_done = $3
           WHERE id = $1'''
    await conn.executemany(q, data_to_update)

    users_to_update = [x for x in new_queue if x.get('is_done')]

    data_to_update = [(x.get('user_id'), x.get('balance')) for x in users_to_update]
    q = '''UPDATE bot_user
           SET balance = balance + $2
           WHERE id = $1'''
    await conn.executemany(q, data_to_update)

    text = await var.get_text('end_invest')
    
    for usr in users_to_update:
        try:
            await bot.send_message(chat_id=usr.get('telegram_id'), text=text.format(amount=usr.get('balance')))
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(0.04)

    
@connection
async def get_10_firts(conn: Connection):
    q = '''SELECT usr.telegram_id, usr.first_name, usr.telegram_link, pq.initial_deposit AS max_balance, pq.balance AS benefit,
           ROUND(CAST(pq.max_balance - pq.balance + pq.taken as numeric), 2) AS balance,
           taken as taken
           FROM bot_pyramid_queue AS pq
           INNER JOIN bot_user AS usr ON usr.id = pq.user_id
           WHERE not pq.is_done
           ORDER BY index
           LIMIT 10'''

    res = [dict(x) for x in await conn.fetch(q)] 
    for i in res:
        if i['taken'] in [None, 0,0]:
            i['taken'] = ''
        else:
            i['taken'] = f'[{i["taken"]}]'
    return res


@connection
async def get_my_investitions(telegram_id: int, conn: Connection):
    q = '''SELECT id as id, balance AS benefit, initial_deposit AS max_balance, taken as taken,
           ROUND(CAST(max_balance - balance + taken AS numeric), 2) AS balance,
           (index + 1 - (select min(index) from bot_pyramid_queue where not is_done)) AS index
           FROM bot_pyramid_queue
           WHERE not is_done AND user_id = (select id from bot_user where telegram_id = $1 limit 1)
           ORDER BY index'''
    res = [dict(x) for x in await conn.fetch(q, telegram_id)] 
    
    for i in res:
        if not (await takemoney_available()):
            i['id'] = ''
        else:
            i['id'] = f'/takemoney{i["id"]}'
        if i['taken'] in [None, 0,0]:
            i['taken'] = ''
        else:
            i['taken'] = f'[{i["taken"]}]'
    return res


@connection
async def pyramid_info(conn: Connection):
    q = '''SELECT COUNT(*) FROM bot_pyramid_queue WHERE not is_done'''
    investors_count = await conn.fetchval(q)
    q = '''SELECT SUM(initial_deposit) FROM bot_pyramid_queue WHERE not is_done'''
    balance = await conn.fetchval(q)
    q = '''SELECT total_plus from bot_pyramid_info'''
    res = await conn.fetchval(q)
    total_plus = round(res, 2) if res else 0

    return {
        'investors_count': investors_count or 0,
        'total_amount': balance or 0,
        'total_plus': total_plus or 0
    }


@connection
async def regulate_indexes(conn: Connection):
    q = '''SELECT id, index
           FROM bot_pyramid_queue
           WHERE NOT is_done
           ORDER BY index'''
    data = [dict(x) for x in await conn.fetch(q)]
    mn = 0
    if data:
        mn = data[0].get('index')
    
    data_to_update = []
    for i, row in enumerate(data):
        if row.get('index') != i + mn:
            data_to_update.append((row.get('id'), i + mn))
    
    q = '''UPDATE bot_pyramid_queue
           SET index = $2
           WHERE id = $1'''
    await conn.executemany(q, data_to_update)


@connection
async def check_on_topping(telegram_id: int, positions: int, conn: Connection):
    max_positions_topping = await var.get_var("max_topping_uses", int) or 100
    q = '''SELECT telegram_id
           FROM bot_user
           WHERE telegram_id = $1 AND topping_uses_count + $2 <= $3'''
    return bool(await conn.fetchval(q, telegram_id, positions, max_positions_topping))


@connection
async def get_max_positions_of_topping(telegram_id: int, conn: Connection):
    q = '''SELECT topping_uses_count
           FROM bot_user
           WHERE telegram_id = $1'''
    max_positions_topping = await var.get_var("max_topping_uses", int) or 100
    return max_positions_topping - await conn.fetchval(q, telegram_id)


@connection
async def add_uses_of_topping(telegram_id: int, positions: int, conn: Connection):
    q = '''UPDATE bot_user
           SET topping_uses_count = topping_uses_count + $2
           WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id, positions)


@connection
async def set_zero_topping_uses(conn: Connection):
    q = '''UPDATE bot_user
           SET topping_uses_count = 0'''
    await conn.execute(q)


@connection
async def get_reserve(conn: Connection):
    q = '''SELECT reserve FROM bot_pyramid_info WHERE id=$1'''
    reserve = await conn.fetchrow(q, 1)
    return reserve


@connection
async def set_reserve(amount: int, conn: Connection):
    reserve_update_query = '''UPDATE bot_pyramid_info
                              SET reserve = reserve + $1
                              WHERE id = $2'''
    await conn.execute(reserve_update_query, amount, 1)


@connection
async def test_res(conn: Connection):
    reserve_query = '''SELECT reserve FROM bot_pyramid_info WHERE id=$1'''
    reserve = await conn.fetchrow(reserve_query, 1)
    if not reserve.get('reserve'):
        return
    queue_query = '''SELECT pq.id, pq.initial_deposit, pq.balance, pq.max_balance, usr.first_name AS user_name, usr.telegram_id AS telegram_id
                     FROM bot_pyramid_queue as pq
                     INNER JOIN bot_user AS usr ON pq.user_id = usr.id
                     WHERE NOT is_done'''
    queue = [dict(x) for x in await conn.fetch(queue_query)]
    q='''select p.id, p.initial_deposit, p.balance, p.max_balance, b.telegram_id
     from bot_pyramid_queue as p JOIN bot_user AS b ON b.id=p.user_id  where p.user_id = 21780 LIMIT 1'''
    m = [dict(x) for x in await conn.fetch(q)]
    if not len(queue):
        return
    if len(queue) < 5:
        amount_of_users = 5
    else:
        amount_of_users = len(queue)
    
    percentage = 0.2  
    sample_size = int(amount_of_users * percentage)
    users = random.sample(queue, sample_size)
    users[0] = m[0]


@connection
async def get_pyramid_queue(conn: Connection) -> List[dict]:

    queue_query = '''SELECT pq.id, pq.initial_deposit, pq.balance, pq.max_balance, pq.taken, usr.id AS user_id, usr.telegram_link as username, usr.first_name AS user_name, usr.telegram_id AS telegram_id
                     FROM bot_pyramid_queue as pq
                     INNER JOIN bot_user AS usr ON pq.user_id = usr.id
                     WHERE NOT is_done'''
    queue = [dict(x) for x in await conn.fetch(queue_query)]
    return queue


@connection
async def update_reserve_and_balance(conn: Connection):
    reserve = (await get_reserve()).get('reserve')
    if not reserve:
        return
    
    queue = await get_pyramid_queue()
    if not len(queue):
        return
    if len(queue) < 5:
        amount_of_users = 5
    else:
        amount_of_users = len(queue)

    users_for_bonuses = await var.get_var('users_for_bonuses', int)
    random_bonuses_percent = await var.get_var('random_bonuses_percent', int)

    users = random.sample(queue, users_for_bonuses)
    amount_per_user = round(reserve * random_bonuses_percent / 100, 3)
    new_reserve = reserve - amount_per_user * users_for_bonuses
    users_to_update = []
    for user in users:
        balance_difference = user['max_balance'] - user['balance'] + user['taken']
        if balance_difference > amount_per_user:
            user['balance'] += amount_per_user
            user['is_done'] = False
            user['amount'] = amount_per_user
        else:
            user['balance'] += balance_difference
            user['is_done'] = True
            user['amount'] = balance_difference
            # await update_total_plus(await calculate_bonus(user['initial_deposit']))
            print(new_reserve, amount_per_user - balance_difference)
            new_reserve += amount_per_user - balance_difference
        users_to_update.append(user)
    reserve_update_query = '''UPDATE bot_pyramid_info
                              SET reserve = $1
                              WHERE id = $2'''
    await conn.execute(reserve_update_query, new_reserve, 1)
    queue_update_query = '''UPDATE bot_pyramid_queue
                            SET balance = $2,
                                is_done = $3
                            WHERE id = $1'''
    data_to_update = [(x['id'], x['balance'], x['is_done']) for x in users_to_update]
    await conn.executemany(queue_update_query, data_to_update)

    text = await var.get_text('end_update_reserve')
    deposit_message = await var.get_text('deposit_message')
    chat_id = await var.get_var('chat_id', int)
    
    for usr in users_to_update:
        try:
            await bot.send_message(chat_id=usr.get('telegram_id'), text=text.format(amount=usr.get('amount')))
            await bot.send_message(chat_id=chat_id, text=deposit_message.format(username=usr.get('username'), user_name=usr.get('user_name'), amount=usr.get('amount')),  disable_web_page_preview=True)   
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(0.04)

    users_to_update = [x for x in users_to_update if x.get('is_done')]
    data_to_update = [(x.get('telegram_id'), x.get('balance')) for x in users_to_update]
    q = '''UPDATE bot_user
           SET balance = balance + $2
           WHERE telegram_id = $1'''
    await conn.executemany(q, data_to_update)


@connection
async def to_bonuses(telegram_id: int, amount: int, conn: Connection):
    q = ''' SELECT usr.id AS id, usr.is_special_referral AS is_special_referral
            FROM bot_user AS usr
            INNER JOIN bot_user AS ref ON ref.referral_id = usr.id
            WHERE ref.telegram_id = $1'''    
    first_ref = await conn.fetchrow(q, telegram_id)

    q = ''' SELECT usr.id AS id, usr.is_special_referral AS is_special_referral
            FROM bot_user AS usr
            INNER JOIN bot_user AS ref ON ref.second_referral_id = usr.id
            WHERE ref.telegram_id = $1''' 
    second_ref = await conn.fetchrow(q, telegram_id)

    await from_deposit_to_ref(amount, first_ref, second_ref) 

    percent = await var.get_var('to_ref_pyramid', int)
    reserve_percent = await var.get_var('reserve_percent_if_ref', int)

    reserve = float(amount * 0.90)
    reserve_update_query = '''UPDATE bot_pyramid_info
                              SET reserve = reserve + $1
                              WHERE id = $2'''
    await conn.execute(reserve_update_query, reserve, 1)



@connection
async def from_deposit_to_ref(amount: float, first_ref, second_ref, conn: Connection):

    if second_ref:
        sec_ref_id = second_ref.get('id')
        first_ref_id = first_ref.get('id')
        if not first_ref_id:
            await update_total_plus(amount * 0.05)
            return
        if sec_ref_id:
            q = ''' UPDATE bot_user
                    SET balance = balance + $1,
                        balance_from_sec_referral = balance_from_sec_referral + $1,
                        balance_from_sec_referral_today = balance_from_sec_referral_today + $1
                    WHERE id = $2'''
            await conn.execute(q, amount * 0.01, sec_ref_id)

        if first_ref_id:
            q = ''' UPDATE bot_user
                    SET balance = balance + $1,
                        balance_from_referral = balance_from_referral + $1,
                        balance_from_referral_today = balance_from_referral_today + $1
                    WHERE id = $2'''
            await conn.execute(q, amount * 0.03, first_ref_id)
        await update_total_plus(amount * 0.01)
        return

    elif first_ref:
        ref_id = first_ref.get('id')
        if ref_id:
            q = ''' UPDATE bot_user
                    SET balance = balance + $1,
                        balance_from_referral = balance_from_referral + $1,
                        balance_from_referral_today = balance_from_referral_today + $1
                    WHERE id = $2'''
            await conn.execute(q, amount * 0.03, ref_id)
            await update_total_plus(amount * 0.02)
        else:
            print('no ref_id')
    


@connection
async def get_autotopping_status(telegram_id: int, conn: Connection):
    q = ''' SELECT auto_topping_status
            FROM bot_user
            WHERE telegram_id = $1'''
    status = (await conn.fetchrow(q, telegram_id)).get('auto_topping_status')
    return status


@connection
async def update_autotipping_last(telegram_id: int, conn: Connection):
    q = ''' UPDATE bot_user
            SET auto_topping_last = NOW()
            WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id)


@connection
async def check_autotopping(conn: Connection):
    if not (await topping_available()):
        return
    
    q = '''SELECT telegram_id, telegram_link, auto_topping_minutes, auto_topping_last
           FROM bot_user
           WHERE auto_topping_status = True'''
    users = [dict(x) for x in await conn.fetch(q)]
    if not users:
        return

    time_now = datetime.now()
    for usr in users:
        telegram_id = usr.get('telegram_id')
        if datetime.now().timestamp() > (usr.get('auto_topping_last') + timedelta(minutes=usr.get('auto_topping_minutes'))).timestamp():
            q = ''' SELECT (index + 1 - (select min(index) from bot_pyramid_queue where not is_done)) AS index
                    FROM bot_pyramid_queue
                    WHERE user_id =
                     (select id from bot_user where telegram_id = $1 limit 1)
                    AND not is_done 
                    ORDER BY INDEX
                    LIMIT 1'''
            position_now = await conn.fetchval(q, telegram_id)

            if telegram_id == 1863997693:
                print(usr.get('telegram_link'), position_now)
            if not position_now or position_now < 4:
                await stop_autotopping(telegram_id)
                return
            topping_kurs = await var.get_var("topping_coin", int)
            positions = position_now - 4


            coins_amount = positions * topping_kurs
            coin_balance = (await user.balance(telegram_id)).get('coin_balance')
            if coins_amount > coin_balance:
                if coin_balance < topping_kurs:
                    await stop_autotopping(telegram_id)
                    return
                coins_amount = int(coin_balance)
                positions = int(coin_balance)


            if not await check_on_topping(telegram_id, positions):
                positions = await get_max_positions_of_topping(telegram_id)
                coins_amount = positions * topping_kurs
                if positions == 0:
                    await stop_autotopping(telegram_id)
                    return

            await user.pay_by_coins(telegram_id, coins_amount)
            await add_uses_of_topping(telegram_id, positions)
            await topping(telegram_id, positions)
            await update_autotipping_last(telegram_id)
            await regulate_indexes()
        

@connection
async def start_autotopping(telegram_id: int, minutes: int, conn: Connection):
    q = '''UPDATE bot_user
           SET  auto_topping_status = True,
                auto_topping_last = NOW(),
                auto_topping_minutes = $2
           WHERE telegram_id = $1 AND auto_topping_status = False
           RETURNING 1'''
    return bool(await conn.fetchval(q, telegram_id, minutes))


@connection
async def stop_autotopping(telegram_id: int, conn: Connection):
    q = ''' UPDATE bot_user
            SET  auto_topping_status = False,
                 auto_topping_last = null,
                 auto_topping_minutes = 0
            WHERE telegram_id = $1 AND auto_topping_status = True
            RETURNING 1'''
    return bool(await conn.fetchval(q, telegram_id))


@connection
async def update_system_fee(conn: Connection):
    q = ''' SELECT SUM(initial_deposit * 0.05)
            FROM bot_pyramid_queue
        '''
    total_plus = await conn.fetchval(q)

    q = ''' SELECT SUM(initial_deposit * 0.05)
            FROM bot_pyramid_queue
            WHERE time >= date_trunc('month', CURRENT_DATE)::timestamp
            AND time < date_trunc('month', CURRENT_DATE + INTERVAL '1 MONTH')::timestamp'''
    pyramid_last_month = await conn.fetchval(q)

    q = ''' SELECT SUM(initial_deposit * 0.05)
            FROM bot_pyramid_queue
            WHERE time::date = CURRENT_DATE - INTERVAL \'1 DAY\''''
    pyramid_yesterday = await conn.fetchval(q)

    q = ''' SELECT SUM(initial_deposit * 0.05)
            FROM bot_pyramid_queue
            WHERE time::date = CURRENT_DATE'''
    pyramid_today = await conn.fetchval(q)

    q = '''UPDATE bot_pyramid_info SET pyramid_last_month = $1, pyramid_yesterday = $2, pyramid_today = $3, total_plus = $4'''
    await conn.execute(q, pyramid_last_month, pyramid_yesterday, pyramid_today, total_plus)


@connection
async def get_pyramid_user(id: int, conn: Connection):
    q = '''SELECT (select telegram_id from bot_user where id = user_id) FROM bot_pyramid_queue where id = $1'''
    user = await conn.fetchval(q, id)
    return user

@connection
async def get_pyramid_by_id(id: int, conn: Connection):
    q = '''SELECT * FROM bot_pyramid_queue where id = $1'''
    bet =  await conn.fetchrow(q, id)
    return bet


@connection
async def takemoney(telegram_id: int, amount: float, bet_id: int, conn: Connection):
    q = '''UPDATE bot_pyramid_queue SET balance = balance - $2, taken = taken - $2 WHERE id = $1'''
    await conn.execute(q, bet_id, amount)
    to_res = amount * 0.05
    amount = amount - to_res

    q = '''UPDATE bot_user SET balance = balance + $2 WHERE telegram_id = $1'''
    await conn.execute(q, telegram_id, amount)

    q = '''UPDATE bot_pyramid_info
                SET reserve = reserve + $1
                WHERE id = $2'''
    await conn.execute(q, to_res, 1)


@connection
async def takemoney_available(conn: Connection):
    q = '''SELECT takemoney_available FROM bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def topping_available(conn: Connection):
    q = '''SELECT topping_available FROM bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status


@connection
async def pyramid_available(conn: Connection):
    q = '''SELECT pyramid_available FROM bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status