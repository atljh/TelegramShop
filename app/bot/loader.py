import os 
import aiogram
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.schedulers.asyncio import AsyncIOScheduler


bot = Bot(token=os.getenv('BOT_TOKEN'), parse_mode='html')
storage = RedisStorage2(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), db=int(os.getenv('REDIS_DB')))
dp = Dispatcher(bot=bot, storage=storage)
scheduler = AsyncIOScheduler()
