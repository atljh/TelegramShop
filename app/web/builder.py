import os
from app.web.routes import app
from aiohttp import web


async def start_web():
    runner = web.AppRunner(app)
    await runner.setup()
    print(os.getenv('web_host', 'localhost'), ':', int(os.getenv('web_port', 8001)), sep='')
    site = web.TCPSite(runner, os.getenv('web_host', 'localhost'), int(os.getenv('web_port', 8001)))
    await site.start()
