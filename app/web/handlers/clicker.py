import pytz
import json
import aiohttp_jinja2
from hashlib import md5
from datetime import datetime
from aiohttp.web import Request, json_response

from app.bot.loader import bot, dp
from app.database import user, clicker
from app.bot.scheduler import update_bonuses_job

from .utils import safe_parse_webapp_init_data


async def clicker_main(request: Request):
    reserve = await clicker.get_reserve() or 0
    if reserve <= 0:
        reserve = None
    return await aiohttp_jinja2.render_template_async(
        'clicker.html', request, {}
    )

async def web_check_user_data(request: Request):
    """Check and return user data"""
    data = await request.post()
    data = safe_parse_webapp_init_data(dp.bot._token, data["_auth"])
    return json_response({"ok": True, "user": data.as_json()})

async def get_next_run_time(request: Request):
    """Get the next scheduled run time for updating bonuses"""
    next_run_time_str = update_bonuses_job.next_run_time.isoformat()
    return json_response({"nextRunTime": next_run_time_str})

async def get_me(request: Request):
    """Get the current user's information"""
    data = await request.post()
    data = safe_parse_webapp_init_data(dp.bot._token, data["_auth"])
    telegram_id = data['user']['id']
    user = await clicker.get_bot_user(telegram_id)
    return json_response({"ok": True, "user": json.dumps(user)})

async def tap(request: Request):
    data = await request.post()
    data = safe_parse_webapp_init_data(dp.bot._token, data["_auth"])
    telegram_id = data['user']['id']
    user = await clicker.tap(telegram_id)
    return json_response({"ok": True, "user": json.dumps(user)})

async def upgrade_energy_level(request: Request):
    data = await request.post()
    data = safe_parse_webapp_init_data(dp.bot._token, data["_auth"])
    telegram_id = data['user']['id']
    user = await clicker.upgrade_energy_level(telegram_id)
    return json_response({"ok": True, "user": json.dumps(user)})


async def xday(request: Request):
    data = await request.json()
    admin_user = await user.get_admin_user(data.get('admin_id'))
    sign = md5(f"{admin_user.get('email')}:{admin_user.get('username')}:{admin_user.get('id')}".encode()).hexdigest()
    if sign != data.get('sign'):
        return json_response({"status": False})
    await clicker.xday()
    return json_response({"status": True})