from django.db import models
from django.db.models import Sum


"""
    Basic Behavior
    ---------------
    
    - Initialization 
            triggered by Version.create()
    - Updates 
            triggered by a slot in 
                version.slots.filter(employee=employee) 
                is modified.
"""


class VersionEmployee(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='versions')
    version = models.ForeignKey('Version', on_delete=models.CASCADE,
                                         related_name='version_employees')
    slots = models.ManyToManyField('Slot', related_name='version_employees')
    periods = models.ManyToManyField('PayPeriod', related_name='version_employees')
    hours = models.IntegerField(default=0)
    overtime = models.IntegerField(default=0)
    discrepancy = models.IntegerField(default=0)


    def __str__(self):
        return self.employee.name


    class Updater:
        @staticmethod
        def update_periods(instance):
            for period in instance.version.periods.filter(employees=instance.employee):
                if period not in instance.periods.all():
                    instance.periods.add(period)

        @staticmethod
        def update_hours(instance):
            hours = instance.slots.a

        @staticmethod
        def update_overtime(instance):
            instance.overtime = instance.slots.aggregate(Sum('overtime'))['overtime__sum']
            instance.save()