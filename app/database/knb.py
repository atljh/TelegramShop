from asyncpg import Connection
from ._core import connection
from . import var

import os
from time import sleep
import requests
import random
from requests import post
from datetime import datetime, timedelta, date
from threading import Thread
from app.database import user as user_db

from app.bot.loader import bot 
from aiogram.types import CallbackQuery, Message


@connection
async def user_games_statistic(telegram_id: int, conn: Connection):
    q = '''SELECT result FROM bot_knb_bet
           WHERE user_id = (select id from bot_user where telegram_id = $1)'''
    data = [dict(x) for x in await conn.fetch(q, telegram_id)]

    wins = [x.get('result') for x in data if x.get('result') == 'win']
    draws = [x.get('result') for x in data if x.get('result') == 'draw']
    loses = [x.get('result') for x in data if x.get('result') == 'lose']

    return len(wins), len(draws), len(loses)


@connection
async def get_active_games(conn: Connection):
    q = ''' SELECT u.first_name, u.telegram_link, b.amount, k.id, k.currency, k.users_amount
            FROM bot_knb k
            JOIN bot_user u ON u.id = k.host_id
            LEFT JOIN bot_knb_bet b ON b.game_id = k.id AND b.user_id = k.host_id
            WHERE k.status = TRUE
            ORDER BY -k.id
            '''
    data = await conn.fetch(q)

    return data


@connection
async def get_users_amount(id: int, conn: Connection):
    q = ''' SELECT user_id from bot_knb_bet WHERE game_id = $1'''
    data = await conn.fetch(q, id)
    return len(data)


@connection
async def get_users_in_game(knb_id: int, conn: Connection):
    q = ''' SELECT
            (select telegram_link from bot_user where id = user_id),
            (select telegram_id from bot_user where id = user_id),
            item
            FROM bot_knb_bet
            WHERE game_id = $1'''
    data = await conn.fetch(q, knb_id)
    return data


@connection
async def check_user_in_game(telegram_id: int, knb_id: int, conn: Connection):
    q = '''SELECT id FROM bot_knb_bet WHERE user_id = (select id from bot_user where telegram_id = $1) AND game_id = $2'''
    data = await conn.fetchrow(q, telegram_id, knb_id)
    return data


@connection
async def get_game(knb_id: int, conn: Connection):
    q = '''SELECT u.telegram_link, u.first_name, k.id, k.currency, k.users_amount, b.amount, u.telegram_id  
            FROM bot_knb_bet b
            LEFT JOIN bot_knb k ON b.game_id = k.id
            LEFT JOIN bot_user u ON u.id = b.user_id
            WHERE b.game_id = $1'''
    data = await conn.fetchrow(q, knb_id)
    return data


@connection
async def get_game_result(telegram_id: int, knb_id: int, conn: Connection):
    q = '''SELECT result from bot_knb_bet where user_id = (select id from bot_user where telegram_id = $1) AND game_id = $2'''
    result = await conn.fetchrow(q, telegram_id, knb_id)
    return result.get('result')


@connection
async def get_knb_history(telegram_id: int, conn: Connection):
    q = ''' SELECT k.id, b.result, b.amount, k.currency, k.users_amount, u.telegram_link, u.first_name, b.win_amount
            FROM bot_knb_bet b 
            JOIN bot_knb k ON k.id = b.game_id 
            JOIN bot_user u ON u.id = b.user_id 
            WHERE u.telegram_id = $1
            ORDER BY -k.id
            LIMIT 30'''
    data = await conn.fetch(q, telegram_id)
    data = data[::-1]
    return data


@connection
async def save_knb(telegram_id: int, currency: str, amount: float, users_amount: int, item: str, conn: Connection):
    q = '''WITH rows as (INSERT INTO bot_knb(host_id, currency, users_amount, status, time)
        VALUES((select id from bot_user where telegram_id = $1), $2, $3, True, NOW()) RETURNING id)

        INSERT INTO bot_knb_bet(game_id, user_id, amount, item, date)
        VALUES((select id from rows), (select id from bot_user where telegram_id = $1), $4, $5, NOW())
        '''
    await conn.execute(q, telegram_id, currency, users_amount, amount, item)
    return 
    

@connection
async def join_knb(telegram_id: int, knb_id: int, amount: float, item: str, conn: Connection):
    q = '''INSERT INTO bot_knb_bet(game_id, user_id, amount, item, date)
            VALUES($2, (select id from bot_user where telegram_id = $1), $3, $4, NOW())'''

    await conn.execute(q, telegram_id, knb_id, amount, item)
    return


@connection
async def autosearch(amount: float, currency: str, users_amount: int, conn: Connection):
    q = ''' SELECT u.first_name, u.telegram_link, b.amount, k.id, k.currency, k.users_amount
            FROM bot_knb k
            JOIN bot_user u ON u.id = k.host_id
            LEFT JOIN bot_knb_bet b ON b.game_id = k.id AND b.user_id = k.host_id
            WHERE k.status = TRUE AND b.amount = $1 AND k.currency = $2 AND k.users_amount = $3 LIMIT 15'''
    data = await conn.fetch(q, amount, currency, users_amount)
    games = [x for x in data if not await get_users_amount(x.get('id')) == x.get('users_amount')]
    return games


@connection
async def start_game(game_id: int, conn: Connection):
    q = ''' SELECT b.amount, b.item, u.telegram_link, u.first_name, u.id
            FROM bot_knb_bet b 
            JOIN bot_knb k ON k.id = b.game_id 
            JOIN bot_user u ON u.id = b.user_id 
            WHERE k.id = $1'''
    users = await conn.fetch(q, game_id)
    winners = []
    draws = []
    losers = []

    if len(users) == 2:
        if users[0].get('item') == users[1].get('item'):
            draws = users
        else:
            if users[0].get('item') == 'rock' and users[1].get('item') == 'scissors'\
             or users[0].get('item') == 'scissors' and users[1].get('item') == 'paper'\
             or users[0].get('item') == 'paper' and users[1].get('item') == 'rock':
                winners = [users[0]]
                losers = [users[1]]
            else:
                winners = [users[1]]
                losers = [users[0]]
    elif len(users) == 3:
        items = [user.get('item') for user in users]
        if len(set(items)) == 1:
            draws = users
        elif len(set(items)) == 2:

            if items.count('rock') == 2 and 'paper' in items:
                winner_idx = items.index('paper')
                winners = [users[winner_idx]]

            elif items.count('rock') == 2 and 'scissors' in items:
                winner_idx = items.index('rock')
                winners = [user for user in users if user.get('item') == 'rock']

            elif items.count('paper') == 2 and 'scissors' in items:
                winner_idx = items.index('scissors')
                winners = [users[winner_idx]]
                
            elif items.count('scissors') == 2 and 'rock' in items:
                winner_idx = items.index('rock')
                winners = [users[winner_idx]]


            elif items.count('scissors') == 2 and 'paper' in items:
                winner_idx = items.index('scissors')
                winners = [user for user in users if user.get('item') == 'scissors']


            elif items.count('paper') == 2 and 'rock' in items:
                winner_idx = items.index('paper')
                winners = [user for user in users if user.get('item') == 'paper']

            else:
                print('Invalid input')
                draws = users
                return winners, draws, losers, 0
            loser_idx = (winner_idx + 1) % 3
            loser = users[loser_idx]
            losers = [user for user in users if user not in winners]

        elif len(set(items)) == 3:
            draws = users
        else:
            print('Invalid input')
            draws = users
            return winners, draws, losers, 0
    else:   
        print('Invalid number of players')
        return winners, draws, losers, 0
        

    
    total_win_amount = 0
    win_amount = 0
    for user in users:
        total_win_amount += user.get('amount')
    if winners:
        win_amount = (total_win_amount / len(winners)) * 0.98

    data = await get_game(game_id)

    await end_game(winners, draws, losers, game_id)

    return winners, draws, losers, win_amount

@connection
async def end_game(winners: list, draws: list, losers: list, game_id: int, conn: Connection):
    total_win_amount = 0
    for user in winners:
        total_win_amount += user.get('amount')
    for user in losers:
        total_win_amount += user.get('amount')
    for user in draws:
        total_win_amount += user.get('amount')


    if len(winners) in [1, 2]:
        system_fee = total_win_amount * 0.01
        reserve_fee = total_win_amount * 0.01
    else:
        system_fee = 0
        reserve_fee = 0

    data = await get_game(game_id)
    cur = data.get('currency')

    if winners:
        winner_amount = (total_win_amount / len(winners)) * 0.98
        winner_comission = ((total_win_amount / len(winners)) * 0.02) * 100


    if cur == '$':
        for user in winners:
            result = 'win'
            q = '''UPDATE bot_knb_bet SET result = $1, win_amount = $4 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id, winner_amount)
            q = '''UPDATE bot_user SET balance = balance + $1, coin_balance = coin_balance + $3 WHERE id = $2'''
            await conn.execute(q, winner_amount, user.get('id'), winner_comission)

        for user in losers:
            result = 'lose'        
            q = '''UPDATE bot_knb_bet SET result = $1 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id)

        for user in draws:
            result = 'draw'
            q = '''UPDATE bot_knb_bet SET result = $1 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id)
            q = '''UPDATE bot_user SET balance = balance + $1 WHERE id = $2'''
            await conn.execute(q, user.get('amount'), user.get('id'))
            
        q = ''' UPDATE bot_pyramid_info
                SET reserve = reserve + $1
                WHERE id = $2'''
        await conn.execute(q, reserve_fee, 1)

    elif cur == 'coins':
        for user in winners:
            result = 'win'
            q = '''UPDATE bot_knb_bet SET result = $1, win_amount = $4 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id, winner_amount)
            q = '''UPDATE bot_user SET coin_balance = coin_balance + $1 WHERE id = $2'''
            await conn.execute(q, winner_amount, user.get('id'))

        for user in losers:
            result = 'lose'
            q = '''UPDATE bot_knb_bet SET result = $1 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id)

        for user in draws:
            result = 'draw'
            q = '''UPDATE bot_knb_bet SET result = $1 WHERE user_id = $2 AND game_id = $3'''
            await conn.execute(q, result, user.get('id'), game_id)
            q = '''UPDATE bot_user SET coin_balance = coin_balance + $1 WHERE id = $2'''
            await conn.execute(q, user.get('amount'), user.get('id'))


    
    q = '''UPDATE bot_knb SET status = False where id = $1'''
    await conn.execute(q, game_id)
    
    await update_system_fee()

    return


@connection
async def pay_for_game(telegram_id: int, cur: str, amount: float, conn: Connection):
    if cur == 'coins':
        if not await user_db.pay_by_coins(telegram_id, amount):
            return False
        return True
    elif cur == '$':
        bal = await user_db.balance(telegram_id)
        if bal.get('balance') >= amount:
            q = '''UPDATE bot_user
                SET balance = balance - $2
                WHERE telegram_id = $1'''
            await conn.execute(q, telegram_id, amount)
            return True
        else:
            return False


async def get_knb_info(message: Message):
    g = await get_game(int(message.get_args()))

    users_in_room = await get_users_in_game(g.get('id'))
    user_link = await var.get_text('users_knb')
    end_game_template = await var.get_text('knb_end_game')
    users_text = ''
    for usr in users_in_room:
        link = user_link.format(telegram_link = usr.get('telegram_link'), item = usr.get('item'))
        users_text += link + '\n'
    
    new_text = end_game_template.format(
        users = users_text,
        id = g.get('id'),
        amount = g.get('amount'),
        currency = g.get('currency'),
        result = '',
        winners = ''
    )
    await message.answer(text=new_text)
    return


@connection
async def update_system_fee(conn: Connection):
    q = ''' SELECT ROUND(CAST(SUM(win_amount * 0.01) as numeric), 2)
            FROM bot_knb_bet
            WHERE date >= date_trunc('month', CURRENT_DATE)::timestamp
            AND date < date_trunc('month', CURRENT_DATE + INTERVAL '1 MONTH')::timestamp AND result = \'win\' '''
    knb_last_month = await conn.fetchval(q)

    q = ''' SELECT ROUND(CAST(SUM(win_amount * 0.01) as numeric), 2)
            FROM bot_knb_bet
            WHERE date::date = CURRENT_DATE - INTERVAL \'1 DAY\' AND result = \'win\' '''
    knb_yesterday = await conn.fetchval(q)

    q = ''' SELECT ROUND(CAST(SUM(win_amount * 0.01) as numeric), 2)
            FROM bot_knb_bet
            WHERE date::date = CURRENT_DATE AND result = \'win\''''
    knb_today = await conn.fetchval(q)

    q = '''UPDATE bot_pyramid_info SET knb_last_month = $1, knb_yesterday = $2, knb_today = $3 WHERE id = $4'''
    await conn.execute(q, knb_last_month, knb_yesterday, knb_today, 1)


@connection
async def get_generate_knb(id: int, conn: Connection):
    q = '''SELECT users_id, currency, users_amount, users_amount_random, games_amount, amount_from, amount_to from bot_generate_knb WHERE id = $1'''
    data = await conn.fetchrow(q, id)

    users = data.get('users_id').split(' ')
    currency = data.get('currency')
    games_amount = data.get('games_amount')
    amount_from = data.get('amount_from')
    amount_to = data.get('amount_to')
    games_per_user = games_amount / len(users)
    items = ['rock', 'paper', 'scissors']
    users_amount_choices = [2,3]
    games = list(range(games_amount))

    while games:
        for user in users:
            if not games:
                break
            amount = round(random.uniform(amount_from, amount_to), 2)
            if not await pay_for_game(int(user), currency, amount):
                continue
            games.pop(0)
            if data.get('users_amount_random'):
                users_amount = random.choice(users_amount_choices)
            else:
                users_amount = data.get('users_amount')

            item = random.choice(items)
            await save_knb(int(user), currency, amount, users_amount, item)

    return

