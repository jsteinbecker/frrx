from computedfields.models import computed
from django.db import models

from frate.basemodels import BaseWorkday
from frate.empl.models import Employee

from frate.ver.models import Version



class Workday(BaseWorkday):
    version       = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='workdays')
    is_holiday    = models.BooleanField(default=False)
    templated_off = models.ManyToManyField(Employee, related_name='templated_off_days', blank=True)

    @computed(models.ManyToManyField(Employee, related_name='pto_days', blank=True))
    def on_pto(self):
        return self.slots.filter(options__name='PTO').values_list('employee__pk', flat=True)

    @computed(models.ManyToManyField(Employee, related_name='tdo_days', blank=True))
    def on_tdo(self):
        return self.slots.filter(options__name='').values_list('employee__pk', flat=True)

    @computed(models.ManyToManyField(Employee, related_name='on_deck_days', blank=True))
    def on_deck(self):
        return self.slots.filter(options__name='On Deck').values_list('employee__pk', flat=True)

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
    def options(self) -> 'QuerySet[SlotOption]':
        from frate.models import SlotOption
        return SlotOption.objects.filter(pk__in=self.slots.values('options__pk'))

    @property
    def pto_requests(self) -> 'QuerySet[PtoRequest]':
        from frate.models import PtoRequest
        return PtoRequest.objects.filter(date=self.date)

    @property
    def on_tdo(self) -> 'QuerySet[Employee]':
        from frate.models import RoleSlot
        return Employee.objects.filter(slug__in=RoleSlot.objects.filter(sd_id=self.sd_id,
                                                                        type='O') \
                                       .values('leader__role__employees') \
                                       .distinct())

    @property
    def templated_employees(self) -> 'QuerySet[Employee]':
        from frate.models import RoleSlot
        return Employee.objects.filter(slug__in=RoleSlot.objects.filter(sd_id=self.sd_id,
                                                                        type__in=['D','R']) \
                                       .values('leader__role__employees') \
                                       .distinct()) \
                                            .exclude(slug__in=self.on_pto.values('slug'))


