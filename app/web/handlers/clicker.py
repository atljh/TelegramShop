import pytz
import json
import aiohttp_jinja2
from datetime import datetime
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web_response import json_response

from app.bot.loader import bot, dp
from app.database import user, clicker
from app.bot.scheduler import update_bonuses_job
from .utils import safe_parse_webapp_init_data


async def clicker_main(request: Request):
    reserve = await clicker.get_reserve()
    return await aiohttp_jinja2.render_template_async(
        'clicker.html', request, {'reserve': reserve})


async def web_check_user_data(request: Request):
    data = await request.post()
    data = safe_parse_webapp_init_data(
        dp.bot._token, data["_auth"]
    )
    return json_response({"ok": True, "user": data.as_json()})


async def get_next_run_time(request):
    next_run_time_str = update_bonuses_job\
    .next_run_time.isoformat()

    return web.Response(
        text=json.dumps({"nextRunTime": next_run_time_str}),
        content_type='application/json'
    )