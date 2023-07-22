from frate.models import *
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save



@receiver(pre_save, sender=Slot)
def set_streak(sender, instance, **kwargs):
    if instance.pk:
        if instance.employee is not None:
            if instance.workday.sd_id > 0:
                d = instance.workday.get_prev()
                i = 1
                while d and d.slots.filter(employee=instance.employee).exists():
                    d = d.get_prev()
                    i += 1
                instance.streak = i
            else:
                instance.streak = 1
        else:
            instance.streak = 0


@receiver(post_save, sender=Slot)
def build_options(sender, instance, created, **kwargs):

    if created:
        from frate.models import SlotOption
        from frate.empl.models import EmployeeQuerySet

        empls = instance.workday.version.schedule.employees.all() # type: EmployeeQuerySet
        trained = empls.trained_for(instance.shift)


        for employee in trained:
            if employee not in instance.workday.on_pto.all():

                SlotOption.objects.create(slot=instance, employee=employee)


