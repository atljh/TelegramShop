from django.db import models
from django.db.models import Q
from datetime import datetime


_null_blank = {'null': True, 'blank': True}


class Mark(models.Model):
    name = models.CharField(max_length=155, blank=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'


class User(models.Model):
    ip = models.CharField(max_length=256, **_null_blank)
    user_agent = models.TextField(**_null_blank)

    telegram_id = models.BigIntegerField(**_null_blank, unique=True)    
    first_name = models.CharField(max_length=256, **_null_blank)
    last_name = models.CharField(max_length=256, **_null_blank)
    telegram_link = models.CharField(max_length=256, **_null_blank)
    mark = models.ForeignKey(to=Mark, on_delete=models.SET_NULL, **_null_blank) 

    referral = models.ForeignKey(to='self', on_delete=models.SET_NULL, **_null_blank, related_name='referrals')
    second_referral = models.ForeignKey(verbose_name="Реф первого уровня", to='self', on_delete=models.SET_NULL, **_null_blank, related_name='second_referrals')

    joined_at = models.DateTimeField(**_null_blank)

    status = models.CharField(max_length=256)

    balance = models.FloatField(default=0)
    coin_balance = models.FloatField(default=0)
    pyramid_balance = models.FloatField(default=0, null=True)

    balance_from_referral = models.FloatField(default=0)
    balance_from_referral_today = models.FloatField(default=0)

    topping_uses_count = models.SmallIntegerField(default=0)
    
    is_special_referral = models.BooleanField(default=False)
    from_channel_link = models.BooleanField(default=False)
    is_started = models.BooleanField(default=True)

    auto_topping_minutes = models.IntegerField(default=0)
    auto_topping_last = models.DateTimeField(**_null_blank)
    auto_topping_status = models.BooleanField(default=False)


    def __str__(self):
        first_name = self.first_name if self.first_name else ''
        last_name = self.last_name if self.last_name else ''
        if self.telegram_link:
            return f'{first_name} {last_name} {self.telegram_link}'
        else:
            return f'{first_name} {last_name} {self.telegram_link}'


    def account_type(self):
        ip = self.ip
        user_agent = self.user_agent
        if ip is None or user_agent is None:
            return 'single'
        id = self.id 
        resp = User.objects.filter(Q(ip=ip) & ~Q(id=id) & ~Q(telegram_id=None))
        return 'multi' if resp else 'single'
    
    class Meta:
        db_table = 'bot_user'


class Var(models.Model):
    id = models.CharField(max_length=256, primary_key=True)
    value = models.TextField()
    description = models.TextField(**_null_blank)
    
    class Meta:
        db_table = 'bot_var'


class Spam(models.Model):
    DAY_CHOICES = (
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    )
    text = models.TextField()
    image = models.CharField(max_length=256)
    received_count = models.IntegerField(**_null_blank)
    day = models.CharField('День недели', max_length=9,
                    choices=DAY_CHOICES,
                    default="0")
    time = models.TimeField('Время', null=True, blank=True)
    status = models.BooleanField('Статус', default=False)

    class Meta:
        db_table = 'bot_spam'

class SpamStatus(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bot_spam_status'

class AutoAnswer(models.Model):
    keys = models.TextField()
    answer = models.TextField()

    class Meta:
        db_table = 'bot_autoanswer'
    

class BanPoll(models.Model):
    poll_id = models.CharField(max_length=256, primary_key=True)
    user_id = models.BigIntegerField()
    
    for_count = models.IntegerField()

    class Meta:
        db_table = 'bot_banpoll'


class Product(models.Model):
    id = models.CharField(max_length=256, primary_key=True)
    title = models.CharField(max_length=256)

    image = models.CharField(max_length=256, **_null_blank)
    text = models.TextField(**_null_blank)

    is_product = models.BooleanField(default=False)
    price = models.FloatField(**_null_blank)
    link = models.CharField(max_length=256, **_null_blank)
    manual = models.CharField(max_length=256, **_null_blank)

    activation = models.BooleanField(verbose_name='Активация', default=False)
    activation_url = models.CharField(verbose_name='URL для активации', max_length=256, **_null_blank)

    index = models.IntegerField(default=0)
    category = models.ForeignKey(to='self', on_delete=models.CASCADE, **_null_blank)
    
    storage = models.BooleanField(verbose_name='Складчина', default=False)

    
    def __str__(self):
        if self.category is None:
            return f'{self.title}'
        else:
            if self.is_product:
                return f'{self.category}-{self.title}-{self.price} $'
            else:
                return f'{self.category}-{self.title}'
    class Meta:
        db_table = 'bot_product'


class SpamProduct(models.Model):
    spam = models.ForeignKey(to=Spam, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)

    class Meta:
        db_table = 'bot_spam_product'


class Purchase(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)

    referral_payed = models.BooleanField("Процент выплачен", default=False, null=True)

    activated = models.BooleanField(default=False)
    created_at = models.DateTimeField()


    class Meta:
        db_table = 'bot_purchase'


class Promocode(models.Model):
    code = models.CharField(max_length=256, primary_key=True)
    use_count = models.SmallIntegerField()
    discount = models.SmallIntegerField()

    class Meta:
        db_table = 'bot_promocode'


class Payment(models.Model):
    telegram_id = models.BigIntegerField()
    checked = models.BooleanField()
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'bot_payment'


class PaymentGateway(models.Model):
    id = models.CharField(max_length=256, primary_key=True)
    title = models.CharField(max_length=256)
    percent = models.FloatField(default=10)
    is_showed = models.BooleanField()

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'bot_payment_gateway'


class WithdrawGateway(models.Model):
    id = models.CharField(max_length=256, primary_key=True)
    title = models.CharField(max_length=256)
    is_showed = models.BooleanField()

    class Meta:
        db_table = 'bot_withdraw_gateway'
        

class WithdrawRequest(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, **_null_blank)
    gateway = models.ForeignKey(to=WithdrawGateway, on_delete=models.SET_NULL, **_null_blank)
    address = models.TextField()
    amount = models.IntegerField()

    created_at = models.DateTimeField()
    status = models.CharField(max_length=256, choices=(
        (None, 'Не обработан'),
        ('ok', 'Одобрить'),
        ('bad', 'Отказать')
    ), **_null_blank)


    class Meta:
        db_table = 'bot_withdraw_request'


class PyramidQueue(models.Model):
    index = models.IntegerField()

    balance = models.FloatField()
    max_balance = models.FloatField()
    initial_deposit = models.FloatField(default=0)
    user = models.ForeignKey(to=User, **_null_blank, on_delete=models.SET_NULL)
    is_done = models.BooleanField()
    time = models.DateTimeField(**_null_blank)

    taken = models.FloatField(verbose_name='Забрано', default=0)

    class Meta:
        db_table = 'bot_pyramid_queue'


class PyramidInfo(models.Model):
    reserve             = models.FloatField(verbose_name='Резерв', default=0)
    total_plus          = models.FloatField(verbose_name='Заработано всего (пирамида)', default=0, **_null_blank)

    pyramid_last_month  = models.FloatField(verbose_name='Зработано на пирамиде за последние 30 дней', default=0, **_null_blank)
    pyramid_yesterday   = models.FloatField(verbose_name='Зработано на пирамиде вчера', default=0, **_null_blank)
    pyramid_today       = models.FloatField(verbose_name='Зработано на пирамиде сегодня', default=0, **_null_blank)

    knb_last_month      = models.FloatField(verbose_name='Зработано на кнб за последние 30 дней', default=0, **_null_blank)
    knb_yesterday       = models.FloatField(verbose_name='Зработано на кнб вчера', default=0, **_null_blank)
    knb_today           = models.FloatField(verbose_name='Зработано на кнб сегодня', default=0, **_null_blank)

    coins_available     = models.BooleanField(verbose_name='Покупка коинов', default=True)
    takemoney_available = models.BooleanField(verbose_name='Забрать деньги', default=True)
    topping_available   = models.BooleanField(verbose_name='Поднятие', default=True)

    pyramid_available   = models.BooleanField(verbose_name='Пирамида', default=True)

    chat_available      = models.BooleanField(verbose_name='Чат активен', default=True)
    games_available     = models.BooleanField(verbose_name='Игры', default=True)

    withdraw_available  = models.BooleanField(verbose_name='Вывод', default=True)
    exchange_available  = models.BooleanField(verbose_name='Обмен', default=True)
    history_available   = models.BooleanField(verbose_name='История', default=True)
    shop_available      = models.BooleanField(verbose_name='Магазин', default=True)

    register_for_storage = models.BooleanField(verbose_name='Записать на складчину', default=True)
    
    buy_pyrtoken_available = models.BooleanField(verbose_name='Купить PyrToken', default=True)
    
    enter_chat_by_ip = models.BooleanField(verbose_name='Вход в чат с ip', default=False)

    class Meta:
        verbose_name = "Pyramid Info"
        verbose_name_plural = "Pyramid Info"
        
        db_table = 'bot_pyramid_info'



class SpecialReferral(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, unique=True)
    link = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'bot_special_referral'


class StartAnswer(models.Model):
    start_link = models.CharField(max_length=256)
    text = models.TextField()
    image = models.CharField(max_length=256)

    def __str__(self):
        return self.start_link

    class Meta:
        db_table = 'bot_start_answer'


class ChannelLinksAutoAnswer(models.Model):
    channel_link = models.CharField(max_length=255, **_null_blank)
    text = models.TextField(**_null_blank)
    image = models.CharField(max_length=256, **_null_blank)
    mark = models.ForeignKey(to=Mark, on_delete=models.CASCADE, **_null_blank) 

    start_answer = models.ForeignKey(to=StartAnswer, on_delete=models.CASCADE, **_null_blank)
    button = models.BooleanField("Добавить кнопку", default=False)
    button_text = models.TextField("Текст кнопки", blank=True)

    def __str__(self):
        return self.channel_link

    class Meta:
        verbose_name = "Channel links auto answer"
        verbose_name_plural = "Channel links auto answers"

        db_table = 'auto_accept_application'



class Deposit(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    payment_gateway = models.ForeignKey(to=PaymentGateway, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    time = models.DateTimeField()

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "Deposit"
        verbose_name_plural = "Deposits"

        db_table = 'deposit'


class ExchangeHistory(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    time = models.DateTimeField()

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "Exchange History"
        verbose_name_plural = "Exchange Histories"

        db_table = 'bot_exchange_history'


class Kurs(models.Model):

    api_kurs = models.FloatField(default=0)
    personal_kurs = models.FloatField(default=0)
    fixed = models.BooleanField(default=False)

    def __str__(self):
        if self.fixed:
            return str(self.personal_kurs)
        return str(self.api_kurs)
    
    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurs"

        db_table = 'bot_kurs'


class PaymentData(models.Model):

    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    invoice_id = models.CharField(max_length=255, unique=True)
    pyramid = models.BooleanField(default=False)

    def __str__(self):
        return self.user


    class Meta:

        db_table = 'bot_payment_data'


class Knb(models.Model):
    CURRENCY_CHOICES = (
        ('$', '$'),
        ('coins', 'coins'),
    )
    host = models.ForeignKey(to=User, on_delete=models.CASCADE, **_null_blank)

    currency = models.CharField('Валюта', max_length=9,
                choices=CURRENCY_CHOICES,
                default="0")
    users_amount = models.IntegerField(default=2)
    status = models.BooleanField(verbose_name='Активная', default=False)
    time = models.DateTimeField()

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = "Game Knb"
        verbose_name_plural = "Games Knb"

        db_table = "bot_knb"


class KnbBet(models.Model):
    ITEM_CHOICES = (
        ('rock', 'Камень'),
        ('paper', 'Бумага'),
        ('scissors', 'Ножницы'),
    )

    RESULT_CHOICES = (
         ('win', 'Win'),
         ('draw', 'Draw'),
         ('lose', 'Lose')
    )
    game = models.ForeignKey(to=Knb, on_delete=models.CASCADE, **_null_blank)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    item = models.CharField(choices=ITEM_CHOICES, max_length=8, **_null_blank)
    amount = models.FloatField(default=0)
    result = models.CharField(choices=RESULT_CHOICES, max_length=8, **_null_blank)
    win_amount = models.FloatField(default=0, **_null_blank)

    date = models.DateTimeField(**_null_blank)
    
    def __str__(self):
        return str(self.game)

    class Meta:
        verbose_name = "Knb Bet"
        verbose_name_plural = "Knb Bets"

        db_table = "bot_knb_bet"


class GenerateKnb(models.Model):
    CURRENCY_CHOICES = (
        ('$', '$'),
        ('coins', 'coins'),
    )
    
    users_id = models.TextField('Telegaram id пользователей')
    currency = models.CharField('Валюта', max_length=9,
                choices=CURRENCY_CHOICES,
                default="0")
    users_amount = models.IntegerField('Количество игроков', default=2)
    users_amount_random = models.BooleanField('Рандомное количество игроков', default=False)
    games_amount = models.IntegerField('Количество игр', default=1)
    amount_from = models.FloatField("Сумма от", default=0)
    amount_to = models.FloatField("Сумма до", default=0)

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = "Generate Knb"
        verbose_name_plural = "Generate Knb"

        db_table = "bot_generate_knb"


class CryptobotPayment(models.Model):
    invoice_id = models.BigIntegerField(default=0)
    telegram_id = models.BigIntegerField()
    amount = models.FloatField(default=0)
    status = models.BooleanField()
    time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bot_cryptobot_payment'





class StartAnswerProduct(models.Model):
    start_answer = models.ForeignKey(to=StartAnswer, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'bot_start_answer_product'
