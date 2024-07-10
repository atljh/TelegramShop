from asyncpg import Connection
from ._core import connection


@connection
async def add(user_id: int, gateway: str, address: str, amount: int, conn: Connection = None):
    q = '''INSERT INTO bot_withdraw_request(user_id, gateway_id, address, amount, created_at, status)
           VALUES((select id from bot_user where telegram_id = $1), 
                  (select id from bot_withdraw_gateway where id = $2), 
                  $3, $4, NOW(), NULL)'''
    await conn.execute(q, user_id, gateway, address, amount)


@connection
async def get_gateways(conn: Connection = None):
    q = '''SELECT id, title
           FROM bot_withdraw_gateway
           WHERE is_showed'''

    return [dict(x) for x in await conn.fetch(q)]
