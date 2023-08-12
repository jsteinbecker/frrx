from computedfields.models import computed
from django.db import models
from django.db.models import QuerySet

from frate.basemodels import BaseWorkday
from frate.empl.models import Employee

from frate.ver.models import Version


class Workday (BaseWorkday):
    version       = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='workdays')
    is_holiday    = models.BooleanField(default=False)
    templated_off = models.ManyToManyField(Employee, related_name='templated_off_days', blank=True)

    @property
    def on_deck(self):
        slots = set(self.slots.filter(employee__isnull=False).values_list('employee__pk', flat=True))
        on_pto = set(self.pto_requests.values_list('employee__pk', flat=True))
        on_tdo = set(self.on_tdo.values_list('pk', flat=True))
        excluded = slots.union(on_pto).union(on_tdo)
        return self.version.schedule.employees.exclude(pk__in=excluded)

    class Meta:
        ordering = ['date']

    @property
    def percent(self):
        if self.slots.count() == 0:
            return 0
        return int((self.slots.filter(employee__isnull=False).count() / self.slots.count()) * 100)

    @property
    def percent_display(self):
        return f'{int(self.percent)}%'

    @property
    def options(self):
        from frate.models import SlotOption
        return SlotOption.objects.filter(pk__in=self.slots.values('options__pk'))

    @property
    def pto_requests(self):
        from frate.pto.models import PtoRequest
        return PtoRequest.objects.filter(date=self.date)

    @property
    def on_tdo(self) -> 'QuerySet[Employee]':
        from frate.models import RoleSlot
        return Employee.objects.filter(slug__in=RoleSlot.objects \
                                       .filter(sd_id=self.sd_id,
                                               leader__type='O') \
                                       .values('leader__role__employees') \
                                       .distinct())

    @property
    def department(self):
        return self.version.schedule.department

    @property
    def on_pto(self):
        from frate.pto.models import PtoRequest
        return PtoRequest.objects.filter(
            date=self.date, employee__department=self.department).select_related('employee')

    @property
    def in_slot(self):
        return self.slots.filter(employee__isnull=False).select_related('employee')

    @property
    def templated_employees(self) -> 'QuerySet[Employee]':
        from frate.models import RoleSlot
        return Employee.objects.filter(slug__in=RoleSlot.objects.filter(sd_id=self.sd_id,
                                                                        leader__type__in=['D', 'R']) \
                                       .values('leader__role__employees') \
                                       .distinct()) \
                                            .exclude(slug__in=self.on_pto.values('slug'))

    def get_next(self) -> BaseWorkday:
        if next_wd := self.version.workdays.filter(sd_id__gt=self.sd_id):
            return next_wd.first()
        return None

    def get_prev(self) -> BaseWorkday:
        if prev_wd := self.version.workdays.filter(sd_id__lt=self.sd_id):
            return prev_wd.last()
        return None
