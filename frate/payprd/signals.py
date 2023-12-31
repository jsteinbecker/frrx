from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from frate.models import *
from frate.payprd.models import PayPeriod



@receiver(post_save, sender=PayPeriod)
def create_needed_pto_slots(sender, instance, **kwargs):

    goal = instance.goal or 0

    if instance.hours < goal:
        for workday in instance.version.workdays.filter(pd_id=instance.pd_id):
            if workday.pto_requests.filter(employee=sender.employee).exists():
                pto_slot = PtoSlot.objects.get_or_create(
                    workday=workday,
                    employee=instance.employee,
                    hours=instance.employee.pto_hours,
                    period=instance,
                    request=workday.pto_requests.filter(employee=instance.employee).first())
                pto_slot[0].save()

