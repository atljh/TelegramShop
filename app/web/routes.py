import aiohttp_jinja2
import jinja2
from aiohttp import web

from app.web.loader import app
from app.web import handlers

app.router.add_post('/spam', handlers.spam)
app.router.add_post('/pay_ref', handlers.pay_ref)
app.router.add_get('/payment_callback', handlers.fowpay_payment_callback)
app.router.add_get('/freekassa_payment_callback', handlers.freekassa_payment_callback)
app.router.add_get('/freekassa_payment_redirect', handlers.freekassa_payment_redirect)
app.router.add_get('/chat_redirect', handlers.chat_redirect)
app.router.add_post ('/cryptocloud_payment_callback3Rs4F8JWskMrLp2AxA2UY8Us', handlers.cryptocloud_payment_callback)
app.router.add_post('/generate_knb', handlers.generate_knb)
app.router.add_get('/distribute_reserve', handlers.distribute_reserve)
app.router.add_post('/xday', handlers.xday)
app.router.add_get('/user_has_access_channel', handlers.user_has_access_channel)

app.router.add_post('/payok_payment_callback', handlers.payok_payment_callback)

#CLICKER
app.router.add_get('/clicker', handlers.clicker_main)

app.router.add_post('/api/me', handlers.get_me)
app.router.add_post('/api/tap', handlers.tap)
app.router.add_post('/api/buy', handlers.upgrade_energy_level)
app.router.add_get('/api/next_run_time', handlers.get_next_run_time)

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('app/web/templates'), enable_async=True)
