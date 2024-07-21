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
async def get_reserve(conn: Connection) -> int:
    q = '''SELECT total_plus FROM bot_pyramid_info'''
    reserve = await conn.fetchval(q)
    return int(reserve * 10000) # To xcoins

@connection
async def get_bot_user(telegram_id: int, conn: Connection) -> dict:
    q = '''
    SELECT 
        bot_user.telegram_link, 
        bot_user.xcoins, 
        current_level.level AS energy_level, 
        current_level.energy_amount AS total_energy_amount, 
        bot_user.energy_amount,
        next_level.cost AS next_level_cost,
        next_level.energy_amount AS next_level_energy
    FROM 
        bot_user 
    JOIN 
        admin_panel_energylevel AS current_level
    ON 
        bot_user.energy_level_id = current_level.id
    LEFT JOIN 
        admin_panel_energylevel AS next_level
    ON 
        next_level.level = current_level.level + 1
    WHERE 
        bot_user.telegram_id = $1;
    '''
    user = await conn.fetchrow(q, telegram_id)
    reserve = await get_reserve()
    user = dict(user) if user else None
    user.update({'reserve': reserve, 'next_level_cost': user.get('next_level_cost')/10000})
    return user

@connection
async def get_user_energy(telegram_id: int, conn: Connection) -> bool:
    q = '''
    SELECT 
        energy_amount 
    FROM 
        bot_user 
    WHERE 
        bot_user.telegram_id = $1
    '''
    energy_amount = await conn.fetchval(q, telegram_id)
    return energy_amount > 0

@connection
async def tap(telegram_id: int, conn: Connection) -> dict:
    xcoins_for_click = await var.get_var('xcoins_for_click', int)
    user_have_energy = await get_user_energy(telegram_id)
    if not user_have_energy or not (await get_reserve()):
        return await get_bot_user(telegram_id)
    q = '''
    UPDATE bot_user
    SET xcoins = xcoins + $1,
        energy_amount = energy_amount - 1 
    WHERE telegram_id = $2;
    '''
    await conn.execute(q, xcoins_for_click, telegram_id)
    return await get_bot_user(telegram_id)

@connection
async def upgrade_energy_level(telegram_id: int, conn: Connection) -> dict:
    user = await get_bot_user(telegram_id)
    user_xcoins = user.get('xcoins')
    user_energy_level = int(user.get('energy_level'))
    if user_energy_level == 7:
        return await get_bot_user(telegram_id)
    next_energy_level = user_energy_level + 1
    
    q = '''
    SELECT
        id, cost
    FROM
        admin_panel_energylevel
    WHERE level = $1
    '''
    next_energy_level_obj = await conn.fetchrow(q, next_energy_level)
    level_id = next_energy_level_obj.get('id')
    level_cost = next_energy_level_obj.get('cost')
    q = '''
    UPDATE
        bot_user
    SET
        energy_level_id = $2,
        xcoins = xcoins - $3
    WHERE
        telegram_id = $1 
    AND
        xcoins - $3 >= 0
    RETURNING 1
    '''
    res = bool(await conn.execute(q, telegram_id, level_id, level_cost))
    if res:
        level_cost_in_dollar = level_cost / 10000 * 0.5
        q = '''
        UPDATE
            bot_pyramid_info
        SET
            reserve = reserve + $1,
            total_plus = total_plus + $1
        '''
        await conn.execute(q, level_cost_in_dollar)
    return await get_bot_user(telegram_id)
    
    
@connection
async def update_energy(conn: Connection):
    q = '''
    '''
    