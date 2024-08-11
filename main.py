import asyncio
import logging

from app.bot.builder import start_bot
from app.web.builder import start_web

loop = asyncio.get_event_loop()
loop.create_task(start_bot())
loop.create_task(start_web())
loop.run_forever()
