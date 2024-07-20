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
    q = '''SELECT telegram_link, xcoins, (select level as energy_level from admin_panel_energylevel where id = bot_user.energy_level_id) FROM bot_user WHERE telegram_id = $1'''
    user = await conn.fetchrow(q, telegram_id)
    return dict(user) if user else None

@connection
async def tap(telegram_id: int, conn: Connection):
    q = '''UPDATE bot_user
           SET xcoins = xcoins + 1'''
    await conn.execute(q)