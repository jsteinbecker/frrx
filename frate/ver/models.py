import datetime

from django.db import models
from django.db.models import Max
from django.urls import reverse
from computedfields.models import ComputedFieldsModel, computed


class VersionScoreCard(ComputedFieldsModel):
    version          = models.OneToOneField('Version', on_delete=models.CASCADE, related_name='scorecard', null=True, blank=True)
    @computed(models.IntegerField(default=0))
    def n_empty_slots(self):
        return self.version.slots.filter(employee__isnull=True).count()

    def __str__(self):
        return f'{self.version} ScoreCard'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Version(ComputedFieldsModel):
    class StatusChoices(models.TextChoices):
        D = 'D', 'Draft'
        P = 'P', 'Published'
        A = 'A', 'Archived'

    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='versions')
    n        = models.PositiveSmallIntegerField()
    status   = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.D)

    @computed(models.IntegerField(default=0))
    def percent(self):
        if self.pk and self.slots.count() > 0:
            return int(self.slots.filter(employee__isnull=False).count() / self.slots.count() * 100)
        else:
            return 0

    def __str__(self):
        return f'{self.schedule}:V{self.n}'

    class Meta:
        ordering = ['n', 'status']

    def display_name(self):
        return f'Schedule {self.schedule.year}-{self.schedule.n}, Version #{self.n}'

    def save(self, *args, **kwargs):
        created = not self.pk

        if not created:
            if self.slots.count() > 0:
                self._update_percent()

        super().save(*args, **kwargs)

        if not self.workdays.exists(): self._build_workdays()
        if not self.periods.exists():  self._build_periods()


    def _build_workdays(self):
        day_count = self.schedule.department.schedule_week_length * 7
        sd = self.schedule.start_date
        if isinstance(sd, str):
            sd = datetime.datetime.strptime(sd, '%Y-%m-%d')
        weekday = sd.strftime('%w')
        for i in range(1, day_count + 1):
            wk_id = (i - 1) // 7 + 1
            pd_id = (i - 1) // 14 + 1
            wd = self.workdays.create(date=sd + datetime.timedelta(days=i - 1),
                                      sd_id=i,
                                      wk_id=wk_id,
                                      pd_id=pd_id,
                                      )
            wd.save()
    def _build_periods(self):
        pd_ids = list(set(self.workdays.values_list('pd_id', flat=True).distinct()))
        print(pd_ids)
        for pd_id in pd_ids:
            for empl in self.schedule.employees.all():
                p = self.periods.create(employee=empl, pd_id=pd_id, goal=empl.fte * 80, hours=0)
                p.save()
    def _update_percent(self):
        self.percent = int((self.slots.filter(employee__isnull=False).count() / self.slots.count()) * 100)

    @property
    def url(self):
        return reverse('dept:sch:ver:detail', kwargs={
            'dept': self.schedule.department.slug,
            'sch': self.schedule.slug,
            'ver': self.n, })

    @property
    def is_best(self):
        return self.percent == self.schedule.versions.aggregate(Max('percent'))['percent__max']

    def assign_positive_templates(self):
        from frate.wday.models import Workday
        for wd in Workday.objects.filter(pk__in=self.slots.filter(direct_template__isnull=False) \
                .values('workday').distinct()):
            wd.assign_direct_template()
        for wd in Workday.objects.filter(pk__in=self.slots.filter(rotating_templates__isnull=False) \
                .values('workday').distinct()):
            wd.assign_rotating_templates()

    def assign_required_backfills(self):
        for slot in self.slots.backfill_required().filter(employee__isnull=True):
            options = slot.options.filter(has_block=False)
            for option in options:
                if not option.employee.role_slots.filter(type='O').exists():
                    if not slot.workday.pto_requests.filter(employee=option.employee).exists():
                        slot.set_employee(option,filled_by='M')
                        slot.save()
                        print('Backfill completed')
                        break

    def solve(self):
        self.assign_positive_templates()
        self.assign_required_backfills()

        for slot in self.slots.filter(employee__isnull=True):
            slot.solve()