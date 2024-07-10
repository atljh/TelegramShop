from asyncpg import Connection
from ._core import connection


@connection
async def get_for_menu(product_id: str, conn: Connection = None):
    q = '''SELECT image, text 
           FROM bot_product
           WHERE NOT is_product AND id = $1
           ORDER BY index'''
    data = await conn.fetchrow(q, product_id)
    if not data:
        return None

    text = data.get('text')
    image = data.get('image')

    q = '''SELECT id, title, is_product, price
           FROM bot_product
           WHERE category_id = $1
           ORDER BY index'''
    data = await conn.fetch(q, product_id)

    items = list()
    for i in data:
        id = i.get('id')
        title = i.get('title')

        if i.get('is_product'):
            id = f'buy_{id}'
            title = f'{title} - {i.get("price")} $'
        items.append(
            {'id': id, 'title': title}
        )
    
    return {'text': text, 'image': image, 'items': items}


@connection
async def get(product_id: str, conn: Connection = None):
    q = '''SELECT image, text, price, link, title, manual, activation, activation_url
           FROM bot_product
           WHERE id = $1 AND is_product
           ORDER BY index
           '''
    data = await conn.fetchrow(q, product_id)
    if data:
        return dict(data)
    return None


@connection
async def is_bought(telegram_id: int, product_id: str, conn: Connection):
    q = '''SELECT product.id
           FROM bot_purchase AS purchase
           INNER JOIN bot_product AS product ON product.id = purchase.product_id
           INNER JOIN bot_user AS usr ON usr.id = purchase.user_id
           WHERE usr.telegram_id = $1 AND product.is_product AND product.id = $2'''
    return await conn.fetchval(q, telegram_id, product_id)



@connection
async def get_category(product_id: str, conn: Connection = None):
    q = '''SELECT category_id
           FROM bot_product
           WHERE id = $1'''
    return await conn.fetchval(q, product_id)


@connection
async def get_product_storage(conn: Connection):
    q = '''SELECT id, image, text, price, link, title, manual, activation, activation_url
        FROM bot_product
        WHERE storage = True AND is_product
        ORDER BY index
        '''
    data = await conn.fetchrow(q)
    if data:
        return dict(data)
    return None
