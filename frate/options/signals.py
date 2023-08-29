from .models import Option
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.db.models import Sum




@receiver(pre_save, sender=Option)
def option_self_update(sender, instance, **kwargs):
    if instance.pk:
        if instance.employee is None: return

        instance.week_hours = instance.employee.slots.filter(
            workday__wk_id=instance.slot.workday.wk_id,
            workday__version=instance.slot.workday.version)\
                .aggregate(Sum('shift__hours'))['shift__hours__sum'] or 0
        instance.period_hours = instance.employee.slots.filter(
            workday__pd_id=instance.slot.workday.pd_id,
            workday__version=instance.slot.workday.version)\
                .aggregate(Sum('shift__hours'))['shift__hours__sum'] or 0


