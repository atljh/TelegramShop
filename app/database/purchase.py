from asyncpg import Connection
from ._core import connection


@connection
async def get(user_id: int, conn: Connection = None):
    q = '''SELECT product.title, product.link, product.id, product.activation, product.manual, purchase.activated
           FROM bot_purchase AS purchase
           INNER JOIN bot_product AS product ON product.id = purchase.product_id
           INNER JOIN bot_user AS usr ON usr.id = purchase.user_id
           WHERE usr.telegram_id = $1 AND product.is_product'''

    return [dict(x) for x in await conn.fetch(q, user_id)]


@connection
async def add(user_id: int, product_id: str, conn: Connection = None):
    q = '''SELECT *
           FROM bot_purchase AS purchase
           INNER JOIN bot_user AS usr ON usr.id = purchase.user_id
           WHERE usr.telegram_id = $1 AND purchase.product_id = $2'''
    if await conn.fetchrow(q, user_id, product_id):
        return 
        
    q = '''INSERT INTO bot_purchase(user_id, product_id, created_at, activated)
           SELECT usr.id, $2, NOW(), False
           FROM bot_user AS usr
           WHERE usr.telegram_id = $1'''

    await conn.execute(q, user_id, product_id)


@connection
async def is_activated(user_id: int, product_id: int, conn: Connection = None):
    q = '''SELECT purchase.activated
           FROM bot_purchase AS purchase
           INNER JOIN bot_product AS product ON product.id = purchase.product_id
           INNER JOIN bot_user AS usr ON usr.id = purchase.user_id
           WHERE usr.telegram_id = $1 AND product.is_product AND purchase.product_id = $2'''

    return await conn.fetchval(q, user_id, product_id)


@connection
async def activate(user_id: int, product_id: int, conn: Connection = None):
       q = '''UPDATE bot_purchase
              SET activated = True 
              WHERE user_id = (select id from bot_user where telegram_id = $1) AND product_id = $2'''
       await conn.execute(q, user_id, product_id)