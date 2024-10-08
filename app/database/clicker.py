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
    reserve = int(reserve * 10000) if reserve else 0 # To xcoins
    return reserve

@connection
async def get_bot_user(telegram_id: int, conn: Connection) -> dict:
    q = '''
    SELECT 
        bot_user.telegram_link, 
        bot_user.balance,
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
    user_row = await conn.fetchrow(q, telegram_id)
    user = dict(user_row) if user_row else None
    reserve = await get_reserve()
    user_energy_level = int(user.get('energy_level'))
    if user_energy_level == 7:
        next_level_cost = None
    else:
        next_level_cost = user.get('next_level_cost')
    user.update(
        {
            'reserve': reserve,
            'next_level_cost': next_level_cost
        }
    )
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
    return energy_amount > 1

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
    
    q = '''
    UPDATE 
        bot_pyramid_info
    SET
        total_plus = total_plus - 0.0001
    '''
    await conn.execute(q)
    return await get_bot_user(telegram_id)

@connection
async def upgrade_energy_level(telegram_id: int, conn: Connection) -> dict:
    user = await get_bot_user(telegram_id)
    user_balance = user.get('balance')
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
    if user_balance < level_cost:
        return await get_bot_user(telegram_id)
        
    q = '''
    UPDATE
        bot_user
    SET
        energy_level_id = $2,
        balance = balance - $3
    WHERE
        telegram_id = $1 
    AND
        balance - $3 >= 0
    RETURNING 1
    '''
    res = bool(await conn.execute(q, telegram_id, level_id, level_cost))
    if res:
        q = '''
        UPDATE
            bot_pyramid_info
        SET
            reserve = reserve + $1,
            total_plus = total_plus + $1
        '''
        await conn.execute(q, level_cost * 0.5)
    return await get_bot_user(telegram_id)
    
    
@connection
async def update_energy(conn: Connection):
    energy_recover_percent = await var.get_var('energy_recover_percent', float)
    q = '''
    SELECT
        id, level, energy_amount
    FROM
        admin_panel_energylevel
    '''
    energy_levels = await conn.fetch(q) 
    for lvl in energy_levels:
        q = '''
        SELECT
            bot_user.telegram_id
        FROM
            bot_user
        JOIN
            admin_panel_energylevel 
        ON
            bot_user.energy_level_id = admin_panel_energylevel.id
        WHERE
            admin_panel_energylevel.id = $1
        AND 
            bot_user.energy_amount < $2;
        '''
        users = await conn.fetch(q, lvl.get('id'), lvl.get('energy_amount'))
        energy_plus = float(lvl.get('energy_amount') * energy_recover_percent / 100)
        energy_plus = round(energy_plus,2)
        for user in users:
            q = '''
            UPDATE
                bot_user
            SET
                energy_amount = CASE
                    WHEN energy_amount + $2 > $3 THEN $3
                    ELSE energy_amount + $2
                END
            WHERE
                telegram_id = $1   
            '''
            await conn.execute(q, user.get('telegram_id'), energy_plus, lvl.get('energy_amount'))
    
    
@connection
async def xday(conn: Connection):
    q = '''
    UPDATE bot_user AS u
    SET energy_level_id = (
        SELECT id
        FROM admin_panel_energylevel AS e
        WHERE e.level = (SELECT level - 1 FROM admin_panel_energylevel WHERE id = u.energy_level_id)
    )
    WHERE EXISTS (
        SELECT 1
        FROM admin_panel_energylevel AS e
        WHERE e.level = (SELECT level - 1 FROM admin_panel_energylevel WHERE id = u.energy_level_id)
    )
    '''
    await conn.execute(q) 
       
    q = '''
    UPDATE bot_pyramid_info
    SET 
        reserve = reserve + (
            SELECT SUM(balance * 0.05)
            FROM bot_pyramid_queue
            WHERE is_done = FALSE
        ),
        total_plus = total_plus + (
            SELECT SUM(balance * 0.05)
            FROM bot_pyramid_queue
            WHERE is_done = FALSE
        )
    WHERE id = 1
    '''
    await conn.execute(q)
    
    q = '''
    UPDATE
        bot_pyramid_queue
    SET 
        initial_deposit = initial_deposit * 0.9,
        balance = balance * 0.9,
        max_balance = max_balance * 0.9
    WHERE is_done = False
    '''
    await conn.execute(q)
    
    
    
@connection
async def zeroing(conn: Connection):
    q = '''BEGIN;

    DELETE FROM bot_pyramid_queue
    WHERE is_done = FALSE;

    WITH first_level AS (
        SELECT id
        FROM admin_panel_energylevel
        WHERE level = 1
        LIMIT 1
    )
    UPDATE bot_user
    SET energy_level_id = (SELECT id FROM first_level);

    UPDATE bot_user
    SET xcoins = 0;

    COMMIT;
    '''
    await conn.execute(q)

        