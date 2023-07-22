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




