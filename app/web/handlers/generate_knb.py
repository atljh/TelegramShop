from aiohttp import web
from aiohttp.web import Request
from app.bot.loader import bot 
from app.database import user, var, knb, pyramid


async def generate_knb(request: Request):
    data = await request.json()
    id = data.get('id')

    await knb.get_generate_knb(id)

    return web.Response(text='ok')


async def distribute_reserve(request: Request):
    await pyramid.update_reserve_and_balance()
    return web.Response(text='ok')
