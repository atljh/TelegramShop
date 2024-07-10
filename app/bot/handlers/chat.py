from aiogram.types import ChatJoinRequest, Message, PollAnswer
from aiogram.dispatcher.storage import FSMContext
from app.database import user, var, system
from datetime import timedelta
from app.bot.loader import bot, dp
from app.bot.utils import buttons, payment, api



async def chat_handler(request: ChatJoinRequest):
    """ Handle join requests for a group or channel """
    status = await user.get_status(request.from_user.id)
    user_id = request.from_user.id
    ip = await user.get_ip(user_id)
    enter_ip = await user.enter_chat_by_ip_available()
    
    channel_link = request.invite_link.invite_link[:-3]

    data = await user.get_channel_link_text(channel_link, user_id)
    if not data:
        await request.approve()
        return
        
    button = data.get('button')
    bot_username = await var.get_text('bot_username')

    if button:
        state = dp.current_state(user=user_id, chat=user_id)
        await state.update_data({'answer_id': data.get('id')})

        reply_markup = buttons.InlineKeyboard(
            {'text': data.get('button_text'), 'data': f'https://t.me/{bot_username}?start={data.get("start_link")}'},
        )
    text = data.get('text', '')
    image = data.get('image', '')

    if text:
        if not image:
            if button:
                await bot.send_message(user_id, text, reply_markup=reply_markup)
            else:
                await bot.send_message(user_id, text)

        else:
            try:
                if button:
                    await bot.send_photo(user_id, photo=image, caption=text, reply_markup=reply_markup)
                else:
                    await bot.send_photo(user_id, photo=image, caption=text)
            except Exception as e:
                print(e)
    else:
        pass
    try:
        if request.chat.type == 'channel':
            await request.approve()
        else:
            if enter_ip:
                print(ip)
                if ip:
                    await request.approve()
                else:
                    await request.decline()
            else:
                await request.approve() 
    except Exception as e:
        print(e)

    if status is None:
        invite_link = request.invite_link.invite_link.strip('.')
        referral_id = str(await user.get_referral_by_link(invite_link))
        telegram_id = request.from_user.id
        first_name = request.from_user.first_name
        last_name = request.from_user.last_name
        telegram_link = request.from_user.username
        
        await user.bot_start(referral_id, telegram_id, first_name, last_name, telegram_link, from_channel_link=True, is_started=False)
        await user.get_channel_link_text(channel_link, user_id)
    
async def auto_answer(message: Message):
    text = (message.text or message.caption).lower().strip()
    answer = await user.check_for_answer(text)
    if answer is None:
        return
    await message.reply(answer)


async def generate_ban(message: Message):
    if not message.reply_to_message:
        await message.answer(await var.get_text('ban_tutorial'))
        return
    
    user_id = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.full_name

    poll = await message.answer_poll(question=(await var.get_text('poll_title')).format(name=name), 
                                     options=['Да', 'Нет'], 
                                     is_anonymous=False,
                                     close_date=timedelta(minutes=await var.get_var('poll_leave_time', int)))
    

    poll_id = poll.poll.id

    await user.create_ban_poll(poll_id, user_id)


async def poll_ban(poll: PollAnswer):
    user_id = poll.user.id
    poll_id = poll.poll_id
    state = dp.current_state(user=user_id, chat=user_id)

    async with state.proxy() as data:
        if data.get(poll_id) == 'ban':
            if poll.option_ids == [1]:
                await user.poll_for_ban(poll_id, inc=-1)
                data[poll_id] = 'unban'
        else:
            if poll.option_ids == [0]:
                data[poll_id] = 'ban'
                resp = await user.poll_for_ban(poll_id)
                if resp is None:
                    return
                
                await bot.ban_chat_member(await var.get_var('chat_id', int), resp, revoke_messages=True)
                await user.set_status(resp, 'report')


