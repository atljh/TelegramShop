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
async def get_reserve(conn: Connection):
    q = '''SELECT total_plus FROM bot_pyramid_info'''
    reserve = await conn.fetchval(q)
    return int(reserve * 10000) # To xcoins