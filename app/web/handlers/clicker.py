import pytz
import json
import aiohttp_jinja2
from datetime import datetime
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web_response import json_response

from app.bot.loader import bot, dp
from app.database import user, product
from app.bot.scheduler import update_bonuses_job
from .utils import safe_parse_webapp_init_data

async def time_to_next_run(job):
    next_run_time = job.next_run_time
    if next_run_time:
        now = datetime.now(pytz.utc)
        
        if next_run_time.tzinfo is None:
            next_run_time = next_run_time.replace(tzinfo=pytz.utc)

        time_remaining = next_run_time - now
        total_seconds = time_remaining.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    else:
        return None

async def clicker(request: Request):
    time = await time_to_next_run(update_bonuses_job)
    return await aiohttp_jinja2.render_template_async(
        'clicker.html', request, {'time_until_bonuses': time})


async def web_check_user_data(request: Request):
    data = await request.post()
    data = safe_parse_webapp_init_data(
        dp.bot._token, data["_auth"]
    )
    return json_response({"ok": True, "user": data.as_json()})


async def get_next_run_time(request):
    next_run_time_str = update_bonuses_job.next_run_time.isoformat()
    # time = await time_to_next_run(update_bonuses_job)
    return web.Response(
        text=json.dumps({"nextRunTime": next_run_time_str}),
        content_type='application/json'
    )