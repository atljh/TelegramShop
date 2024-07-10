from asyncpg import Connection
from ._core import connection


@connection
async def check(code: str, conn: Connection = None):
    q = '''UPDATE bot_promocode
           SET use_count = use_count - 1
           WHERE use_count > 0 AND code = $1
           RETURNING discount'''
    discount = await conn.fetchval(q, code)
    if discount is None:
        return {'status': False, 'discount': 0}
    return {'status': True, 'discount': discount}