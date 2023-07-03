from frate.models import Version, PayPeriod, Slot, Employee, Schedule, Workday
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save


@receiver(post_save, sender=Version)
def build_pay_periods(sender, instance, **kwargs):

    pd_ids = list(set(instance.workdays.values_list('pd_id', flat=True)))

    for pd_id in pd_ids:
        for employee in instance.schedule.employees.all():

            pd = PayPeriod.objects.get_or_create(
                version=instance,
                pd_id=pd_id,
                employee=employee)

            pd[0].save()



