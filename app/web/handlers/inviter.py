from aiohttp import web
from aiohttp.web import Request
from app.bot.loader import bot 
from app.database import user, product


async def user_has_access_channel(request: Request):
    status = await product.is_bought(int(request.query.get('telegram_id')), request.query.get('product_id'))
    print('st', status)
    if not status:
        return web.Response(text='ERROR')
    return web.Response(text='OK')
    
