from asyncpg import Connection
from ._core import connection


async def get_text(text_id: str):
    text = await get_var(text_id, str)
    if not text:
        return 'Undef'
    return text

@connection
async def get_var(var_id: str, type, conn: Connection):
    q = '''SELECT value
           FROM bot_var
           WHERE id = $1'''
    value = await conn.fetchval(q, var_id)
    if value is None:
        return type()
    
    return type(value)

