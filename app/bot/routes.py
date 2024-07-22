from aiogram import types

from app.bot.loader import dp
from app.bot import handlers

rng = list(range(1, 10*10000))

dp.register_message_handler(handlers.start, commands='start', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.reset, commands='reset', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.add_pur, commands='add_pur', state='*', chat_type=[types.ChatType.PRIVATE])

dp.register_message_handler(handlers.pyramid_add, commands='add', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.pyramid_topping, commands='topping', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.regulate_indexes, commands='reg', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.set_zero_positions_topping, commands='set_zero_top', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.dev, commands='dev', state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.set_special_referral, commands='iamspecialreferral', state='*', chat_type=[types.ChatType.PRIVATE])


dp.register_message_handler(handlers.join_knb, commands=[f'startknb{i}' for i in rng], state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.takemoney, commands=[f'takemoney{i}' for i in rng], state='*', chat_type=[types.ChatType.PRIVATE])
dp.register_message_handler(handlers.get_knb, commands='jetknnbgame', state='*', chat_type=[types.ChatType.PRIVATE])

dp.register_callback_query_handler(handlers.register_storage_handler, lambda e: e.data == 'register_for_storage', state='*')

dp.register_callback_query_handler(handlers.useful_services, lambda e: e.data == 'useful_services', state='*')
dp.register_callback_query_handler(handlers.get_chat_link, lambda e: e.data == 'get_chat_link', state='*')
dp.register_callback_query_handler(handlers.check_sub, lambda e: e.data == 'check_sub', state='*')
dp.register_callback_query_handler(handlers.set_profile, lambda e: e.data == 'profile', state='*')
dp.register_callback_query_handler(handlers.main, lambda e: e.data == 'main', state='*')
dp.register_callback_query_handler(handlers.close, lambda e: e.data == 'close', state='*')
dp.register_callback_query_handler(handlers.referral_menu, lambda e: e.data == 'referral', state='*')
dp.register_callback_query_handler(handlers.referral_menu, lambda e: e.data == 'reload_referral', state='*')


dp.register_callback_query_handler(handlers.profile_handler, state='profile')

dp.register_callback_query_handler(handlers.profile_handler, lambda e: e.data == 'finance', state='*')
dp.register_callback_query_handler(handlers.profile_handler, lambda e: e.data == 'withdraw', state='*')
dp.register_callback_query_handler(handlers.profile_handler, lambda e: e.data == 'refill', state='*')
dp.register_callback_query_handler(handlers.profile_handler, lambda e: e.data == 'exchange_pyramid', state='*')
dp.register_callback_query_handler(handlers.profile_handler, lambda e: e.data == 'exchange', state='*')
dp.register_callback_query_handler(handlers.profile_handler, state='select_refill')
dp.register_callback_query_handler(handlers.profile_handler, state='select_exchange')
dp.register_callback_query_handler(handlers.profile_handler, state='exchange_pyramid')

dp.register_callback_query_handler(handlers.manual,lambda e: e.data.startswith('prod_'), state='started')
dp.register_callback_query_handler(handlers.activate,lambda e: e.data.startswith('activate_'), state ='started')
dp.register_callback_query_handler(handlers.activate,lambda e: e.data.startswith('activate_'), state ='input_product_id')
dp.register_message_handler(handlers.input_product_id, state='input_product_id')

dp.register_message_handler(handlers.input_refill_pyramid, state='refill_pyramid')
dp.register_callback_query_handler(handlers.refill_pyramid_handler, state='refill_pyramid')

dp.register_message_handler(handlers.input_refill_amount, state='refill')
dp.register_callback_query_handler(handlers.refill_handler, state='refill')


dp.register_message_handler(handlers.input_exchange_amount, state='exchange')
dp.register_message_handler(handlers.input_sell_coins, state='sell_coins')
dp.register_message_handler(handlers.input_exchange_to_pyramid_amount, state='exchange_to_pyramid')
dp.register_message_handler(handlers.input_exchange_from_pyramid_amount, state='exchange_from_pyramid')


dp.register_message_handler(handlers.input_withdraw_amount, state='withdraw')
dp.register_callback_query_handler(handlers.select_withdraw_gateway, state='select_withdraw_gateway')

dp.register_message_handler(handlers.input_withdraw_address, state='input_withdraw_address')
dp.register_message_handler(handlers.input_withdraw_amount, state='input_withdraw_amount')

dp.register_callback_query_handler(handlers.purchase_menu, lambda e: e.data == 'purchases', state='*')
dp.register_callback_query_handler(handlers.products_menu, lambda e: e.data == 'products', state='*')
dp.register_callback_query_handler(handlers.handle_product, lambda e: e.data in ('buy', 'get'), state='products')
dp.register_callback_query_handler(handlers.products_menu, state='products')

dp.register_callback_query_handler(handlers.check_payment, lambda e: e.data == 'check_payment', state='handle_payment')
dp.register_callback_query_handler(handlers.promocode_handler, lambda e: e.data == 'promocode', state='handle_payment')
dp.register_callback_query_handler(handlers.manual_payment, lambda e: e.data == 'manual_payment', state='handle_payment')
dp.register_callback_query_handler(handlers.pay_from_balance, lambda e: e.data == 'from_balance', state='handle_payment')

dp.register_callback_query_handler(handlers.pyramid_info, lambda e: e.data == 'pyramid_info', state='*')
dp.register_callback_query_handler(handlers.pyramid_info_handler, state='pyramid_info')
dp.register_callback_query_handler(handlers.pyramid_info_handler, lambda e: e.data == 'deposit_balance', state='*')
dp.register_callback_query_handler(handlers.pyramid_info_handler, lambda e: e.data == 'pyramid_history', state='*')
dp.register_callback_query_handler(handlers.pyramid_info_handler, lambda e: e.data == 'topping', state='*')
dp.register_message_handler(handlers.input_invest_amount, state='input_invest_amount')
dp.register_message_handler(handlers.input_invest_coins_amount, state='input_invest_coins_amount')
dp.register_message_handler(handlers.input_topping_positions, state='input_invest_topping')
dp.register_message_handler(handlers.input_minutes_autotopping, state='input_minutes_autotopping')
dp.register_message_handler(handlers.input_takemoney, state='input_takemoney')

dp.register_callback_query_handler(handlers.pyramid_info_handler, lambda e: e.data == 'autotopping', state='*')
dp.register_callback_query_handler(handlers.pyramid_info_handler, lambda e: e.data == 'stop_autotopping', state='*')

dp.register_message_handler(handlers.input_promocode, state='input_promocode')
dp.register_callback_query_handler(handlers.products_menu, state='handle_payment')

dp.register_callback_query_handler(handlers.games_handler, lambda e: e.data == 'games', state='*')
dp.register_callback_query_handler(handlers.games_handler, lambda e: e.data == 'knb', state='*')
dp.register_callback_query_handler(handlers.games_handler, state='games')
dp.register_callback_query_handler(handlers.knb_handler, state='knb')
dp.register_callback_query_handler(handlers.knb_handler, state='create_knb')
dp.register_message_handler(handlers.create_knb, state='create_knb')
dp.register_message_handler(handlers.input_knb_games_amount, state='input_knb_games_amount')
dp.register_message_handler(handlers.input_knb_bet_amount, state='input_knb_bet_amount')



dp.register_callback_query_handler(handlers.products_menu, state='*')


dp.register_message_handler(handlers.generate_ban, commands='ban', chat_type=[types.ChatType.SUPERGROUP, types.ChatType.GROUP], state='*')
dp.register_message_handler(handlers.auto_answer, chat_type=[types.ChatType.SUPERGROUP, types.ChatType.GROUP], state='*')
dp.register_poll_answer_handler(handlers.poll_ban)

dp.register_chat_join_request_handler(handlers.chat)