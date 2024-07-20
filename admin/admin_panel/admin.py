import os

from django.contrib import admin
from .models import *
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.db.models.query import QuerySet
from threading import Thread
from time import sleep
from requests import post, get
from django.utils.html import format_html
from aiohttp import web

from django_object_actions import DjangoObjectActions, action

class AccountTypeFilter(SimpleListFilter):
    title = 'AccountType' # or use _('country') for translated title
    parameter_name = 'account_type'

    def lookups(self, request, model_admin):
        return [('single', 'Одиночные'), ('multi', 'Мульти')]

    def queryset(self, request, queryset: QuerySet):
        queryset = queryset.exclude(telegram_id=None)

        if not self.value():
            return queryset

        users = []
        for user in queryset:
            if user.account_type() == self.value() or not self.value():
                users.append(user.id)
        return queryset.filter(pk__in=users)
                

class PurchaseTabular(admin.TabularInline):
    model = Purchase


def pay_ref(id):
    sleep(3) 
    post(f'http://{os.getenv("web_host", "localhost")}:{os.getenv("web_port", 7000)}/pay_ref', json={'id': id})
    return web.Response(text='ok')

class UserAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('ip', 'balance', 'coin_balance', 'first_name', 'last_name', 'telegram_link', 'joined_at', 'status', 'account_type', 'mark', 'referral',)
    # readonly_fields = ('account_type', 'referral', )
    search_fields = ('id', 'first_name', 'last_name', 'telegram_link', 'telegram_id', 'ip', 'telegram_id', )
    list_filter = ('status', AccountTypeFilter)
    inlines = (PurchaseTabular, )
    
    def account_type(self, obj: User):
        return mark_safe(obj.account_type())
    account_type.short_description = 'Account type'
    account_type.allow_tags = True

    change_actions = ('pay_ref', )

    @action(label="Выплатить процент", description="Выплатить процент")
    def pay_ref(self, request, obj):
        Thread(target=pay_ref, args=[obj.pk]).start()
        
 
class VarAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'description')
    search_fields = ('id', )


def send_spam(id):
    sleep(3) 
    post(f'http://{os.getenv("web_host", "localhost")}:{os.getenv("web_port", 7000)}/spam', json={'id': id})
    return web.Response(text='ok')


class SpamProductTabular(admin.TabularInline):
    model = SpamProduct


class SpamAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('text', 'received_count', 'day', 'time', 'status',)
    inlines = [SpamProductTabular, ]

    @action(label="Начать рассылку", description="Начать рассылку")
    def start_spam(self, request, obj):
        Thread(target=send_spam, args=[obj.pk]).start()


    change_actions = ('start_spam', )

    def save_model(self, request, obj: Spam, form, change):
        obj.save()
        id = obj.pk
        # Thread(target=send_spam, args=[id]).start()


class StartAnswerProductTabular(admin.TabularInline):
    model = StartAnswerProduct


class StartAnswerAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('start_link', 'text',)
    inlines = [StartAnswerProductTabular, ]


class AutoAnswerAdmin(admin.ModelAdmin):
    list_display = ('keys', 'answer')


class ProductTabular(admin.TabularInline):
    model = Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_product', 'price', 'link', 'category')
    inlines = (ProductTabular,)


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')


class PromocodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'use_count', 'discount')


class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'percent', 'is_showed')


class WithdrawGatewayAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_showed')


class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'gateway', 'address', 'amount', 'created_at', 'status')
    readonly_fields = ('user', )
    def save_model(self, request, obj: WithdrawRequest, form, change) -> None:
        if 'status' in form.changed_data:
            if obj.status == 'bad':
                user = obj.user
                user.balance += obj.amount
                user.save()

        return super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
admin.site.register(Var, VarAdmin)
admin.site.register(Spam, SpamAdmin)
admin.site.register(StartAnswer, StartAnswerAdmin)
admin.site.register(AutoAnswer, AutoAnswerAdmin)
admin.site.register(BanPoll)
admin.site.register(Product, ProductAdmin)


admin.site.register(Purchase, PurchaseAdmin)

admin.site.register(Promocode, PromocodeAdmin)
admin.site.register(PaymentGateway, PaymentGatewayAdmin)
admin.site.register(WithdrawGateway, WithdrawGatewayAdmin)
admin.site.register(WithdrawRequest, WithdrawRequestAdmin)


class PyramidQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'index', 'balance', 'max_balance', 'user', 'is_done', 'time', 'taken', )
    readonly_fields = ('user',)

admin.site.register(PyramidQueue, PyramidQueueAdmin)

class SpecialReferralAdmin(admin.ModelAdmin):
    list_display = ("user", "link")
    def get_form(self, request, obj=None, **kwargs):
        form = super(SpecialReferralAdmin, self).get_form(request, obj, **kwargs)            
        form.base_fields["user"].queryset = User.objects.filter(is_special_referral=True)
        return form
admin.site.register(SpecialReferral, SpecialReferralAdmin)


class ChannelLinksAutoAnswerAdmin(admin.ModelAdmin):
    list_display = ('channel_link', 'text', 'mark')
    # list_display = ('channel_link', 'text')

admin.site.register(ChannelLinksAutoAnswer, ChannelLinksAutoAnswerAdmin)


class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_gateway', 'amount', 'time')
    search_fields = ('user__first_name', 'user__last_name', 'user__telegram_link')

admin.site.register(Deposit, DepositAdmin)


class ExchangeHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'time')

admin.site.register(ExchangeHistory, ExchangeHistoryAdmin)


def distribute_reserve():
    get(f'http://{os.getenv("web_host", "localhost")}:{os.getenv("web_port", 7000)}/distribute_reserve')


class PyramidInfoAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('reserve', 'total_plus', 'pyramid_last_month', 'pyramid_yesterday', 'pyramid_today',
     'knb_last_month', 'knb_yesterday', 'knb_today', )

    @action(label="Распределить резерв", description="Распределить резерв")
    def reserve(self, request, obj):
        distribute_reserve()

    change_actions = ('reserve', )

admin.site.register(PyramidInfo, PyramidInfoAdmin)



class KursAdmin(admin.ModelAdmin):
    list_display = ('api_kurs', 'personal_kurs', 'fixed')

admin.site.register(Kurs, KursAdmin)


class KnbBetAdminTabular(admin.TabularInline):
    list_display = ('game', 'user', 'item', 'amount', 'result', )
    readonly_fields = ('user', 'game', )
    model = KnbBet

class KnbAdmin(admin.ModelAdmin):
    inlines = [KnbBetAdminTabular]
    list_display = ('host', 'currency', 'users_amount', 'status', 'time',)
    search_fields = ('host__first_name', 'host__last_name', 'host__telegram_link', 'host__id',
     'knbbet__user__first_name', 'knbbet__user__telegram_link', 'knbbet__user__last_name', 'knbbet__user__id', 'knbbet__user__telegram_id')
    readonly_fields = ('host', )


def generate_knb(id):
    post(f'http://{os.getenv("web_host", "localhost")}:{os.getenv("web_port", 7000)}/generate_knb', json={'id': id})


class GenerateKnbAdmin(DjangoObjectActions, admin.ModelAdmin):
    @action(label="Сгенерировать", description="Сгенерировать игры")
    def publish_this(self, request, obj):
        generate_knb(obj.pk)

    change_actions = ('publish_this', )


admin.site.register(GenerateKnb, GenerateKnbAdmin)
admin.site.register(Knb, KnbAdmin)
admin.site.register(Mark)
admin.site.register(SpamStatus)
admin.site.register(EnergyLevel)