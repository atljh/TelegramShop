from aiohttp import web
from aiohttp.web import Request
from app.bot.loader import bot 
from app.database import user, var


def _get_real_ip(request: Request) -> str:
    return request.headers.get('X-Real-IP',request.remote)

async def chat_redirect(request: Request):
    user_agent = request.headers.get('User-Agent')
    if 'telegram' in user_agent.lower():
        chat_link = await var.get_text('only_chat_link')
        raise web.HTTPFound(chat_link)
        
    ip = _get_real_ip(request)
    id = int(request.query.get('id', -1))
    await user.update_frod(id, ip, user_agent)
    chat_link = await var.get_text('only_chat_link')
    raise web.HTTPFound(chat_link)