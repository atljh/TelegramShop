from .routes import dp
from .scheduler import scheduler
from time import sleep

async def start_bot():
    scheduler.start()
    await dp.start_polling()
