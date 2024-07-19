import aiohttp_jinja2
from aiohttp import web
from aiohttp.web import Request

from app.bot.loader import bot 
from app.database import user, product



async def clicker(request: Request):
    return await aiohttp_jinja2.render_template_async('clicker.html', request, {})