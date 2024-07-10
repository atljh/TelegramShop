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
async def games_available(conn: Connection):
    q = '''SELECT games_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def chat_available(conn: Connection):
    q = '''SELECT chat_available from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status

@connection
async def shop_available(conn: Connection):
    q = '''SELECT shop_available from bot_pyramid_info'''
    status = await conn.fetchval(q)
    return status

@connection
async def register_storage_available(conn: Connection):
    q = '''SELECT register_for_storage from bot_pyramid_info WHERE id = $1'''
    status = await conn.fetchval(q, 1)
    return status