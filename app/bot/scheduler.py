from .loader import scheduler
from app.database import pyramid, user, knb, payment, var
from app.bot import utils
import asyncio


def run_async(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(func(*args, **kwargs))

async def get_bonuses_interval():
    return await var.get_var('bonuses_interval', int)
bonuses_interval = run_async(get_bonuses_interval)


# scheduler.add_job(pyramid.set_zero_topping_uses, 'cron', hour=1, minute=1, second=1)
scheduler.add_job(user.set_zero_referral_balance_today, 'cron', hour=1, minute=1, second=1)
scheduler.add_job(pyramid.regulate_indexes, 'cron', hour=1, minute=1, second=1)

scheduler.add_job(pyramid.update_reserve_and_balance, 'interval', hours=bonuses_interval)

scheduler.add_job(user.check_spam_tasks, 'interval', minutes=5)
scheduler.add_job(user.update_currency_exchange, 'cron', hour=23, minute=59, second=59)
scheduler.add_job(pyramid.update_system_fee, 'interval', minutes=10)
# scheduler.add_job(pyramid.check_autotopping, 'interval', seconds=40)
# scheduler.add_job(knb.update_system_fee, 'interval', minutes=10)

scheduler.add_job(utils.check_cryptobot, 'interval', minutes=5)
scheduler.add_job(payment.delete_cryptobot, 'cron', day=1, hour=23, minute=59, second=59)



# scheduler.add_job(utils.check_p2pkassa, 'interval', minutes=5)
# scheduler.add_job(payment.delete_p2pkassa, 'cron', day=1, hour=23, minute=59, second=59)