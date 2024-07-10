from aiogram.types import Message
from app.database import purchase, pyramid, user, knb



async def add_pur(message: Message):
    product_id = message.get_args()
    await purchase.add(message.from_user.id, product_id)


async def pyramid_add(message: Message):
    amount = int(message.get_args())
    await pyramid.add(message.from_user.id, amount)


async def pyramid_topping(message: Message):
    positions = int(message.get_args())
    await pyramid.topping(message.from_user.id, positions)


async def regulate_indexes(message: Message):
    await pyramid.regulate_indexes()


async def set_zero_positions_topping(message: Message):
    await pyramid.set_zero_topping_uses()


async def dev(message: Message):
    await user.get_same_telergam_id()


async def get_knb(message: Message):
    await knb.get_knb_info(message)