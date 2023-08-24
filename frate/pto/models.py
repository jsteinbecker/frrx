import datetime

from django.core.exceptions import ValidationError
from django.db import models

from frate.empl.models import Employee
from frate.wday.models import Workday


class PtoQuerySet(models.QuerySet):
    def for_employee(self, employee: Employee):
        return self.filter(employee=employee)

    def for_date(self, date: datetime.date):
        return self.filter(date=date)

    def for_employee_and_date(self, employee: Employee, date: datetime.date):
        return self.filter(employee=employee, date=date)

    def employees(self):
        from frate.empl.models import Employee
        return Employee.objects.filter(pk__in=self.values('employee__pk'))

    def dates(self):
        return self.values_list('date', flat=True).distinct()


class PtoManager(models.Manager):
    def get_queryset(self):
        return PtoQuerySet(self.model, using=self._db)

    def for_employee(self, employee: Employee):
        return self.get_queryset().for_employee(employee)

    def for_date(self, date: datetime.date):
        return self.get_queryset().for_date(date)

    def for_employee_and_date(self, employee: Employee, date: datetime.date):
        return self.get_queryset().for_employee_and_date(employee, date)

    def employees(self):
        return self.get_queryset().employees()

    def dates(self):
        return self.get_queryset().dates()


class PtoRequest(models.Model):
    """
    A request for Paid Time Off. PtoRequests exist outside the workdays of versions. They instead
    are translated into PtoSlots, which occupy a relationship with the actual workday objects.
    """
    date = models.DateField()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_requests')

    class StatusChoices(models.TextChoices):
        PENDING  = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        DENIED   = 'D', 'Denied'

    status = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    class Meta:
        ordering = ['date']
        unique_together = ['date', 'employee']

    def __str__(self):
        return f'{self.employee.initials}|{self.date}'

    def clean(self):
        super().clean()
        self._validate_window()
        self._ensure_no_conflicts_in_approved_status()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self._autocreate_ptoslots()

    def _validate_window(self):
        max_window = self.employee.department.pto_max_week_window * 7
        if self.date - datetime.date.today() > datetime.timedelta(days=max_window):
            raise ValidationError(f'PTO request must be within {max_window} days of today')

    def _autocreate_ptoslots(self):
        from frate.models import PtoSlot
        workdays = Workday.objects.filter(
            version__schedule__employees=self.employee,
            date=self.date
        )
        for wd in workdays:
            if wd is not None:
                if not wd.slots.filter(employee=self.employee).exists():
                    if not PtoSlot.objects.filter(employee=self.employee, workday=wd).exists():
                        # CREATE
                        ptoslot = PtoSlot.objects.create(
                            employee=self.employee,
                            workday=wd,
                            hours=self.employee.pto_hours,
                            request=self,
                            period=wd.version.periods.get(pd_id=wd.pd_id, employee=self.employee)
                        )
                        ptoslot.save()

    def _ensure_no_conflicts_in_approved_status(self):
        if self.status == 'A':  # APPROVED status
            if self.employee.pto_requests.filter(date=self.date, status='A').exists():
                raise ValidationError('Employee already has an approved PTO request for this date')

    objects = PtoManager()