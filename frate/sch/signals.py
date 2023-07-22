from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save, post_init

from frate.models import Schedule, Version





@receiver(post_save, sender=Schedule)
def create_version_initial(sender, instance, created, **kwargs):
    if created:
        instance.versions.create(n=1)
        instance._gather_template_slots()



@receiver(post_save, sender=Schedule)
def create_schedules_employee_list(sender, instance, created, **kwargs):
    if created:
        instance.employees.set(instance.department.employees.filter(is_active=True,
                                                                    start_date__lte=instance.start_date))



class VersionInitialSignals:

    @staticmethod
    @receiver(post_save, sender=Version)

    def create_hours_guides(sender, instance, created,**kwargs):
        if created:
            for employee in instance.schedule.employees.filter(fte__lt=1):
                if employee.fte > 0:
                    employee.preferred_hours_guides.create(version=instance,
                                                           hours=employee.fte*80,
                                                           start_date=instance.schedule.start_date)
                else:
                    employee.preferred_hours_guides.create(version=instance,
                                                           hours=10,
                                                           start_date=instance.schedule.start_date)


