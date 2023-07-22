from django.db import models
from django.db.models import Sum

from frate.ver.models import Version
from computedfields.models import ComputedFieldsModel, computed


class PayPeriod(ComputedFieldsModel):
    """
    # PAY PERIOD Model
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

    version  = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='periods', editable=False)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='periods', editable=False)
    pd_id    = models.PositiveSmallIntegerField(editable=False)
    hours    = models.PositiveSmallIntegerField(default=0)

    @computed(models.IntegerField(null=True, blank=True))
    def discrepancy(self):
        return self.hours - self.goal

    @computed(models.IntegerField(null=True, blank=True))
    def goal(self):
        if self.goal is None:
            if self.employee.fte > 0:
                return self.employee.fte * 80
            else:
                return 10
        else:
            return self.goal

    @computed(models.ManyToManyField('SlotOption', blank=True))
    def fill_options(self):
        from frate.models import SlotOption
        slots = SlotOption.objects.filter(pk__in=self.version.slots.filter(pd_id=self.pd_id).values('options'))
        return slots

    class Meta:

        ordering = ['pd_id', 'employee__last_name']

    def __str__(self):
        return f'PayPeriod {self.pd_id} ({self.employee.initials})'

    def start_date(self):
        return self.version.workdays.filter(pd_id=self.pd_id).first().date

    def end_date(self):
        return self.version.workdays.filter(pd_id=self.pd_id).last().date

    def save(self, *args, **kwargs):
        if self.pk:
            for pto in self.employee.pto_slots.filter(workday__version=self.version,
                                                     workday__pd_id=self.pd_id)\
                                            .exclude(period=self):
                self.pto_slots.add(pto)
                pto.save()
            hrs = self.slots.aggregate(Sum('hours'))['hours__sum']
            pto_hrs = self.pto_slots.aggregate(Sum('hours'))['hours__sum']
            if hrs is None: hrs = 0
            if pto_hrs is None: pto_hrs = 0
            if self.hours >= self.goal: self.hours = self.goal
            else: self.hours = hrs + pto_hrs

            self.discrepancy = self.hours - self.goal
            if self.discrepancy < 0:
                self.discrepancy = -1 * self.discrepancy
        super().save(*args, **kwargs)
