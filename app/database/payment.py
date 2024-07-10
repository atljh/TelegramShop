from asyncpg import Connection
from ._core import connection


@connection
async def add(user_id: int, conn: Connection = None):
    q = '''INSERT INTO bot_payment(telegram_id, checked, created_at)
           VALUES($1, FALSE, NOW())'''
    await conn.execute(q, user_id)


@connection
async def check(user_id, conn: Connection = None):
    q = '''UPDATE bot_payment
           SET checked = TRUE
           WHERE NOT checked AND     = $1
           RETURNING telegram_id'''
    return bool(await conn.fetchval(q, user_id))


@connection
async def get_gateways(conn: Connection):
    q = '''SELECT id, title
           FROM bot_payment_gateway
           WHERE is_showed'''
    return [dict(x) for x in await conn.fetch(q)]

@connection
async def check_last(user_id, conn: Connection = None):
	q = '''SELECT *
		   FROM bot_payment
		   WHERE telegram_id = $1 AND NOW() - created_at < INTERVAL '10 min' '''
	return bool(await conn.fetchval(q, user_id))


@connection
async def add_payment_data(telegram_id: int, amount: float, invoice_id: str, pyramid: bool, conn: Connection):
    if not invoice_id:
        return
    q = ''' INSERT INTO bot_payment_data(user_id, amount, invoice_id, pyramid)
            VALUES((select id from bot_user where telegram_id = $1), $2, $3, $4)'''
    await conn.execute(q, telegram_id, amount, invoice_id, pyramid)


@connection
async def get_payment_data(invoice_id: str, conn: Connection):
    q = ''' SELECT (select telegram_id from bot_user where id = user_id), amount, pyramid
            FROM bot_payment_data WHERE invoice_id = $1'''
    return await conn.fetchrow(q, invoice_id)
 

@connection
async def add_cryptobot(invoice_id: int, user_id: int, amount: float, conn: Connection):
    q = '''INSERT INTO bot_cryptobot_payment(telegram_id, amount, status, invoice_id, time)
            VALUES($1, $2, False, $3, NOW())'''
    await conn.execute(q, user_id, amount, invoice_id)


@connection
async def check_cryptobot(conn: Connection):
    q = '''SELECT telegram_id, amount, invoice_id 
           FROM bot_cryptobot_payment WHERE status = False'''
    data = await conn.fetch(q)
    return data


@connection
async def update_cryptobot(invoice_id: int, conn: Connection):
    q = '''UPDATE bot_cryptobot_payment
           SET status = TRUE
           WHERE invoice_id = $1'''
    await conn.execute(q, invoice_id)


@connection
async def delete_cryptobot(conn: Connection):
    q = 'DELETE FROM bot_cryptobot_payment WHERE CAST(time AS DATE) < CURRENT_DATE'''
    await conn.execute(q)
