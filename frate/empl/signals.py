from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db.models import Avg

from .models import Employee, PreferredHoursGuide
from frate.models import Version


@receiver(post_save, sender=Version)
def create_preferred_hours_guide(sender, instance, created, **kwargs):
    if created:
        for employee in instance.schedule.employees.filter(fte=0):

            phg = PreferredHoursGuide.objects.create(
                            version=instance,
                            employee=employee)
            phg.save()

