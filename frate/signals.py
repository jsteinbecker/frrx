from django.db.models import Sum
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save

from .models import *


@receiver(post_save, sender=Role)
def pass_down_employee_to_role_slots(sender, instance, **kwargs):
    employees = instance.employees.all()
    for role_slot in instance.slots.all():
        if role_slot.employees.count() != employees.count():
            role_slot.employees.set(employees)
            role_slot.save()


@receiver(post_save, sender=Slot)
def slot_links_with_period(sender, instance, **kwargs):
    if instance.employee:
        pd_id = instance.workday.pd_id
        period = instance.workday.version.periods.get(pd_id=pd_id, employee=instance.employee)
        if instance.period != period:
            instance.period = period
            instance.save()

    elif not instance.employee:
        if instance.period:
            instance.period = None
            instance.save()


@receiver(post_save, sender=PayPeriod)
def period_calcs_hours(sender, instance, **kwargs):
    if instance.employee:
        hours = instance.slots.aggregate(hours=Sum('shift__hours'))['hours']
        if hours is None:
            hours = 0
        if instance.hours != hours:
            instance.hours = hours
    else:
        if instance.hours != 0:
            instance.hours = 0