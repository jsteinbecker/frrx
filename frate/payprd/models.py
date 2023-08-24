from django.db import models
from django.db.models import Sum, F

from frate.ver.models import Version
from computedfields.models import ComputedFieldsModel, computed


class PayPeriod(ComputedFieldsModel):
    """
    Model
    # PAY PERIOD 
    ==================
    
    An automatic grouping of an employee's slots for a given pay period.

    Creation:   Time of Schedule Version Initialization
    Deletion:   Time of Schedule Version Deletion
    Updates:    On any slot changing hands for the employee within the pay period
    Usage:      Helps ensure guaranteed hours, proper shift distribution, and minimization of Overtime


    ## Fields

    - version
    - employee
    - pd_id `<int>`
    - hours `<int>`
    - goal `<int>`
    - discrepancy `<int>`
    - fill_options
    """
    version  = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='periods')
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='periods')
    pd_id    = models.PositiveSmallIntegerField(editable=False)
    hours    = models.PositiveSmallIntegerField(default=0)
    discrepancy = models.IntegerField(null=True, blank=True)
    goal     = models.PositiveSmallIntegerField(null=True, blank=True)

    @property
    def workdays(self):
        return self.version.workdays.filter(pd_id=self.pd_id)

    class Meta:

        ordering = ['pd_id', 'discrepancy', 'employee']

    def __str__(self):
        return f'PayPeriod {self.pd_id} ({self.employee.initials})'

    def start_date(self):
        return self.version.workdays.filter(pd_id=self.pd_id).first().date

    def end_date(self):
        return self.version.workdays.filter(pd_id=self.pd_id).last().date

    class Updater:

        @staticmethod
        def clean_goal(self):
            if self.goal is None:
                override = self.version.schedule.employee_hours_overrides.filter(employee=F('employee'))
                if override.exists():
                    self.goal = override.first().hours
                else:
                    self.goal = self.employee.fte * 80
            else:
                self.goal = self.employee.fte * 80

        @staticmethod
        def clean_discrepancy(self):
            if self.goal is not None:
                self.discrepancy = self.goal - self.hours
            else: self.discrepancy = self.goal

        @staticmethod
        def clean_hours(self):
            if self.version and self.pk:
                self.hours = self.slots.aggregate(Sum('shift__hours'))['shift__hours__sum'] or 0

    def clean(self):
        self.Updater.clean_goal(self)
        self.Updater.clean_hours(self)
        self.Updater.clean_discrepancy(self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
