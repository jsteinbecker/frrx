from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save, post_init

from frate.models import Version
from frate.sch.models import Schedule


@receiver(post_save, sender=Schedule)
def create_version_initial(sender, instance, created, **kwargs):
    if created:
        instance.versions.create(n=1)
        instance.save()
        instance._gather_template_slots()


@receiver(post_save, sender=Schedule)
def create_schedules_employee_list(sender, instance, created, **kwargs):
    if created:
        instance.employees.set(instance.department.employees.filter(is_active=True,
                                                                    start_date__lte=instance.start_date))


@receiver(post_save, sender=Schedule)
def create_schedules_shift_list(sender, instance, created, **kwargs):
    if created:
        instance.shifts.set(instance.department.shifts.filter(is_active=True))


@receiver(post_save, sender=Schedule)
def create_schedules_role_list(sender, instance, created, **kwargs):
    if created:
        instance.roles.set(instance.department.roles.filter(active=True))


@receiver(post_save, sender=Schedule)
def create_hours_overrides(sender, instance, created, **kwargs):
    if created:
        for employee in instance.employees.filter(std_hours_override__gt=0):
            override = instance.employee_hours_overrides.create(employee=employee,
                                                                hours=employee.std_hours_override)
            override.save()


