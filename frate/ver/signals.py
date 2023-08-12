from frate.basemodels import Weekday
from frate.models import Slot
from frate.sch.models import Schedule
from frate.wday.models import Workday
from frate.empl.models import Employee
from frate.payprd.models import PayPeriod
from frate.ver.models import Version, VersionScoreCard
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save

import datetime


@receiver(post_save, sender=Version)
def build_workdays(sender, instance, created, **kwargs):

    if not created: return
    
    day_count  = instance.schedule.department.schedule_week_length * 7
    start_date = instance.schedule.start_date
    
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        
    initial_weekday = int(start_date.strftime('%w'))
    for i in range(1, day_count + 1):
        weekday = (initial_weekday + i - 1) % 7
        wk_id = (i - 1) // 7 + 1
        pd_id = (i - 1) // 14 + 1
        wd = instance.workdays.create(
                                    date=start_date + datetime.timedelta(days=i - 1),
                                    sd_id=i,
                                    wk_id=wk_id,
                                    pd_id=pd_id,
                                    weekday=Weekday.objects.get(n=weekday)
                                )
        wd.save()


@receiver(post_save, sender=Version)
def build_pay_periods(sender, instance, created, **kwargs):

    if not created: return

    for i in range(1, instance.workdays.count() // 14 + 1):
        for empl in instance.schedule.department.employees.all():
            pd = PayPeriod.objects.create(
                version=instance,
                pd_id=i,
                employee=empl,
            )
            pd.save()


@receiver(post_save, sender=Version)
def build_scorecard(sender, instance, created, **kwargs):
    if not created: return

    if not VersionScoreCard.objects.filter(version=instance).exists():
        card = VersionScoreCard.objects.create(version=instance)
        card.save()

