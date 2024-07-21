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
        admin_panel_energylevel.level AS energy_level, 
        admin_panel_energylevel.energy_amount AS total_energy_amount, 
        bot_user.energy_amount
    FROM 
        bot_user 
    JOIN 
        admin_panel_energylevel 
    ON 
        bot_user.energy_level_id = admin_panel_energylevel.id
    WHERE 
        bot_user.telegram_id = $1
    '''
    user = await conn.fetchrow(q, telegram_id)
    return dict(user) if user else None


@connection
async def tap(telegram_id: int, conn: Connection):
    xcoins_for_click = await var.get_var('xcoins_for_click', int)
    
    q = '''
    UPDATE bot_user
    SET xcoins = xcoins + $1,
        energy_amount = energy_amount - 1
    '''
    await conn.execute(q, xcoins_for_click)

@connection
async def update_energy(conn: Connection):
    q = '''
    '''
    