from django.db import models
from django.dispatch import Signal


class Option(models.Model):
    """
    OPTION (model)
    A Fill Option for a Slot
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='options')
    slot = models.ForeignKey('Slot', on_delete=models.CASCADE, related_name='options')
    pay_period = models.ForeignKey('PayPeriod', on_delete=models.CASCADE, related_name='options', null=True, blank=True)
    entitled = models.BooleanField(default=False)
    discrepancy = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.employee} {self.slot}'

    class Meta:
        verbose_name = 'Option'
        verbose_name_plural = 'Options'
        ordering = ['slot', '-entitled', '-discrepancy']
        unique_together = ['employee', 'slot']


    class Updater:
        @staticmethod
        def clean_pay_period(self):
            prd = self.slot.version.periods.filter(
                                pd_id=self.slot.workday.pd_id,
                                employee=self.employee)
            if prd.exists():
                return prd.first()
            else:
                return None

        @staticmethod
        def clean_week_hours(self):
            return self.slot.version.slots.filter(
                                employee=self.employee,
                                workday__wk_id=self.slot.workday.wk_id)\
                                .aggregate(models.Sum('shift__hours'))['shift__hours__sum'] or 0

        @staticmethod
        def clean_period_hours(self):
            return self.slot.version.slots.filter(
                                employee=self.employee,
                                workday__pd_id=self.slot.workday.pd_id)\
                                .aggregate(models.Sum('shift__hours'))['shift__hours__sum'] or 0

        @staticmethod
        def clean_entitled(self):
            return self.slot.direct_template == self.employee

        @staticmethod
        def clean_discrepancy(self):
            if self.slot.version.schedule.employee_hours_overrides.filter(employee=self.employee).exists():
                goal = self.slot.version.schedule.employee_hours_overrides.get(employee=self.employee).hours
            else:
                goal = self.employee.fte * 80
            if self.pay_period:
                self.pay_period.save()
                hours = self.pay_period.hours
            else:
                hours = 0
            return hours - goal



    updater = Updater()


    def clean(self):
        if not self.pay_period:
            self.pay_period = self.updater.clean_pay_period(self)
        self.week_hours = self.updater.clean_week_hours(self)
        self.period_hours = self.updater.clean_period_hours(self)
        self.entitled = self.updater.clean_entitled(self)
        self.discrepancy = self.updater.clean_discrepancy(self)


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
