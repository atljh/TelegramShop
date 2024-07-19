import aiohttp_jinja2
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web_response import json_response

from app.bot.loader import bot, dp
from app.database import user, product

from .utils import safe_parse_webapp_init_data

async def clicker(request: Request):
    return await aiohttp_jinja2.render_template_async('clicker.html', request, {})


async def web_check_user_data(request: Request):
    data = await request.post()
    data = safe_parse_webapp_init_data(dp.bot._token, data["_auth"])
    return json_response({"ok": True, "user": data.as_json()})
