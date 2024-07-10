from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone

from .models import Mark, User, Purchase, Spam, SpamStatus

import datetime

@login_required()
def statistic(request):
    mark_users = User.objects.all().count()
    purchases = Purchase.objects.all()
    earned = Purchase.objects.aggregate(total_earned=Sum('product__price'))['total_earned'] or 0
    suc_spam = SpamStatus.objects.all()

    marks = Mark.objects.all()
    data = {
        'mark_users': mark_users,
        'purchases': purchases.count(),
        'earned': earned,
        'suc_spam': suc_spam.count(),
    
        'marks': marks,
        }

    return render(request, 'statistic.html', data)


@login_required()
def statistic_api(request):
    mark = request.GET.get('mark')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')


    if start_date_str:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        start_date = timezone.now() - timezone.timedelta(days=300)

    if end_date_str:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        end_date = timezone.now()

    if mark == 'all' or not mark:
        mark_users = User.objects.all().filter(joined_at__range=(start_date, end_date))
        purchases = Purchase.objects.all().filter(created_at__range=(start_date, end_date))
        earned = Purchase.objects.filter(created_at__range=(start_date, end_date)).aggregate(total_earned=Sum('product__price'))['total_earned'] or 0
        suc_spam = SpamStatus.objects.filter(date__range=(start_date, end_date))

    else:
        mark_users = User.objects.filter(mark__id=mark).filter(joined_at__range=(start_date, end_date))
        purchases = Purchase.objects.filter(user__mark__id=mark).filter(created_at__range=(start_date, end_date))
        earned = Purchase.objects.filter(user__mark__id=mark).filter(created_at__range=(start_date, end_date)).aggregate(total_earned=Sum('product__price'))['total_earned'] or 0
        suc_spam = SpamStatus.objects.filter(user__mark__id=mark).filter(date__range=(start_date, end_date))

    
    marks = Mark.objects.all()

    data = {
        'mark_users': mark_users.count(),
        'purchases': purchases.count(),
        'earned': earned,
        'suc_spam': suc_spam.count(),
    
        }

    return JsonResponse(data=data)

