import datetime

from computedfields.models import ComputedFieldsModel
from django.db import models
from django.urls import reverse
from .basemodels import AutoSlugModel, BaseEmployee, BaseSchedule, EmployeeTemplateSetBuilderMixin, BaseWorkday, Weekday
from frate.slot.models import Slot
from .empl.models import Employee
from .payprd.models import PayPeriod
from .pto.models import PtoRequest
from .role.models import Role
from .sch.models import Schedule
from .sft.models import Shift
from .ver.models import Version
from .wday.models import Workday
from .solution.models import SolutionAttempt
from .profile.models import ProfileVerificationToken
from django.contrib.auth.models import User
from .options.models import Option
from frate.ver.ver_empl.models import VersionEmployee

COLOR_CHOICES = [
    ('amber', 'Amber'),
    ('blue', 'Blue'),
    ('sky', 'Sky'),
    ('teal', 'Teal'),
    ('green', 'Green'),
    ('indigo', 'Indigo'),
    ('purple', 'Purple'),
    ('zinc', 'Gray')
]


# Create your models here.
class Organization(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)

    def __str__(self): return self.name


class TimePhase(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)
    end_time = models.TimeField()
    rank = models.PositiveSmallIntegerField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='phases')
    icon_id = models.CharField(max_length=300, null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True, choices=COLOR_CHOICES)

    def __str__(self): return self.name

    class Meta:
        ordering = ['end_time']
        verbose_name = 'Phase'
        verbose_name_plural = 'Phases'

    def save(self, *args, **kwargs):
        if not self.rank:
            self.rank = self.organization.phases.filter(end_time__lt=self.end_time).count()
        super().save()


class Department(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    schedule_week_length = models.PositiveSmallIntegerField(default=6)
    initial_start_date = models.DateField(default='2023-02-05')
    icon_id = models.CharField(max_length=300, null=True, blank=True, verbose_name='Icon',
                               help_text='IconID (referenced via Iconify)')
    image = models.FilePathField(max_length=500, path='static/media/', null=True, blank=True)
    pto_max_week_window = models.PositiveSmallIntegerField(default=52,
                                            help_text='Maximum number of weeks in the future that PTO can be requested')

    def __str__(self): return self.name

    def get_first_unused_start_date(self) -> datetime.date:
        start_date = self.initial_start_date
        while self.schedules.filter(start_date=start_date).exists():
            start_date += datetime.timedelta(days=self.schedule_week_length * 7)
        return start_date


    def get_absolute_url(self):
        return reverse('dept:detail', kwargs={'dept': self.slug})

    url = property(get_absolute_url)


class ShiftTraining(models.Model):
    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    effective_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    rank = models.PositiveSmallIntegerField(default=0)
    rank_percent = models.PositiveSmallIntegerField(default=0)

    def __str__(self): return f'{self.employee.initials}:{self.shift} Training'

    class Meta:
        ordering = ['rank']
        verbose_name = 'Shift Training'
        verbose_name_plural = 'Shift Trainings'

    def save(self, *args, **kwargs):
        n_trainings = self.employee.shifttraining_set.count()
        rank_percent = self.rank / n_trainings
        self.rank_percent = int(rank_percent * 100)
        super().save(*args, **kwargs)



class PtoSlot(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_slots')
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='pto_slots')
    hours = models.IntegerField(default=8)
    request = models.ForeignKey(PtoRequest, on_delete=models.CASCADE, related_name='pto_slots')
    period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='pto_slots', null=True, blank=True)

    def __str__(self):
        return f'<{self.employee.initials}> PTO Slot:{self.workday.date.strftime("%M/%d")}'

    def set_hours(self):
        if self.hours != self.employee.pto_hours:
            self.hours = self.employee.pto_hours
            self.save()

    def set_period(self):
        if not self.period:
            if self.workday.version.periods.filter(pd_id=self.workday.pd_id,
                                                   employee=self.employee,
                                                   version=self.workday.version).exists():
                self.period = self.workday.version.periods.get(pd_id=self.workday.pd_id,
                                                               employee=self.employee,
                                                               version=self.workday.version)
                self.save()

    def clean(self):
        super().clean()
        self.set_hours()
        self.set_period()

    def save(self, *args, **kwargs):
        if self.pk:
            self.full_clean()
        super().save(*args, **kwargs)



class EmployeeTemplateScheduleQuerySet(models.QuerySet):

    def active(self): return self.filter(status='A')

    def inactive(self): return self.filter(status='I')



class EmployeeTemplateScheduleManager(models.Manager):
    def get_queryset(self): return EmployeeTemplateScheduleQuerySet(self.model, using=self._db)

    def active(self): return self.get_queryset().active()

    def inactive(self): return self.get_queryset().inactive()



class EmployeeTemplateSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='template_schedules')

    class StatusChoices(models.TextChoices):
        A = 'A', 'Active'
        I = 'I', 'Inactive'

    status = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.A)

    def __str__(self):
        return f'{self.employee} TemplateSchedule:{self.status}'

    class Meta:
        ordering = ['employee', 'status']

    def save(self, *args, **kwargs):
        created = not self.pk
        if created:
            ts = self.employee.template_schedules.filter(status='A')
            if ts.exists():
                ts.update(status='I')
        super().save(*args, **kwargs)
        if not self.template_slots.exists():
            sch_days = self.employee.department.schedule_week_length * 7
            ts_days = self.employee.template_week_count
            max_ts_day = ts_days * 7
            if created:
                for i in range(sch_days):
                    if i < max_ts_day:
                        s = self.template_slots.create(sd_id=i + 1,
                                                       employee=self.employee,
                                                       type='G'
                                                       )
                        s.save()
                    else:
                        s = self.template_slots.create(sd_id=i + 1,
                                                       employee=self.employee,
                                                       type='G',
                                                       following=self.template_slots.get(sd_id=i % max_ts_day + 1)
                                                       )
                        s.save()

    def display_template_slot_types(self):
        import json
        array = [slot.type for slot in self.template_slots.all()]
        return json.dumps(array)

    objects = EmployeeTemplateScheduleManager()



class BaseTemplateSlot(models.Model):
    template_schedule = models.ForeignKey(EmployeeTemplateSchedule, on_delete=models.CASCADE,
                                          related_name='template_slots')
    sd_id = models.PositiveSmallIntegerField()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='template_slots')
    direct_shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='direct_template_slots', null=True,
                                     blank=True)
    rotating_shifts = models.ManyToManyField(Shift, related_name='rotating_template_slots')
    following = models.ForeignKey('self', on_delete=models.CASCADE, related_name='followers', null=True, blank=True)
    schedules = models.ManyToManyField(Schedule, related_name='template_slots')

    class DTSTypeChoices(models.TextChoices):
        DIRECT = 'D', 'Direct'
        ROTATING = 'R', 'Rotating'
        GENERIC = 'G', 'Generic'
        OFF = 'O', 'Templated Off'

    type = models.CharField(max_length=1, choices=DTSTypeChoices.choices, default=DTSTypeChoices.DIRECT)

    def __str__(self):
        return f'Template {self.sd_id} {self.employee.initials} {self.type}'

    class Meta:
        ordering = ['sd_id']

    def check_options(self):
        options = []
        for shift in self.employee.shifts.filter(weekdays="SMTWRFA"[self.sd_id % 7]):
            if not BaseTemplateSlot.objects.filter(template_schedule__is_active=True,
                                                   sd_id=self.sd_id,
                                                   direct_shift=shift.shift) \
                    .exclude(employee=self.employee).exists():
                options.append(shift.shift)
            if options:
                return Shift.objects.filter(pk__in=options)
            else:
                return Shift.objects.none()

    def save(self, *args, **kwargs):
        created = not self.pk

        def correct_type():
            if self.type == 'T':
                self.type == 'O'

        correct_type()
        super().save(*args, **kwargs)

        self.template_schedule.save()
        for follower in self.followers.all():
            follower.direct_shift = self.direct_shift
            follower.rotating_shifts.set(self.rotating_shifts.all())
            follower.type = self.type
            follower.schedules.set(self.schedules.all())
            follower.save()



class RoleLeaderSlot(models.Model):
    sd_id = models.PositiveSmallIntegerField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='leader_slots')
    type = models.CharField(max_length=1,
                            choices=Role.TemplateTypeChoices.choices,
                            default=Role.TemplateTypeChoices.GENERIC)
    shifts = models.ManyToManyField(Shift, related_name='leader_slots')

    def __str__(self):
        return f'{self.role} {self.sd_id} {self.type}'

    def shifts_on_day(self):
        print(self.sd_id)
        weekday = Weekday.objects.get(n=self.sd_id % 7)
        return weekday.shifts.filter(department=self.role.department)

    def unassigned_shifts(self):
        # get shifts that are unassigned in every child roleSlot
        shifts = self.shifts_on_day()
        for slot in self.slots.all():
            shifts = shifts.exclude(pk__in=slot.shifts.all())
        return shifts

    def _construct_slots(self):
        n_cycles = self.role.cycles_per_schedule()
        cycle_length = self.role.week_count * 7

        for i in range(n_cycles):
            s = self.slots.create(sd_id=self.sd_id + (i * cycle_length), )
            s.save()

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)

        if not self.slots.exists():
            self._construct_slots()

        if self.type in ['O', 'G']:
            self.shifts.clear()
            for slot in self.slots.all():
                if slot.shifts.count() > 0:
                    slot.shifts.clear()

        for slot in self.slots.all():
            slot.shifts.set(self.shifts.all())
            slot.save()



class RoleSlot(models.Model):
    leader = models.ForeignKey(RoleLeaderSlot, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    sd_id = models.PositiveSmallIntegerField()
    shifts = models.ManyToManyField(Shift, related_name='role_slots')
    employees = models.ManyToManyField(Employee, related_name='role_slots')

    class Meta:
        ordering = ['sd_id']

    def __str__(self):
        return f'RoleSlot|{self.sd_id}{self.leader.type}|'

    def unassigned_shifts(self):
        weekday = Weekday.objects.get(n=(self.sd_id - 1) % 7)
        shifts = weekday.shifts.filter(department=self.leader.role.department)
        assigned = shifts.filter(role_slots__sd_id=self.sd_id, role_slots__leader__type=self.leader.type).values('pk')
        return shifts.exclude(pk__in=assigned)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if not self.shifts.exists():
            self.shifts.set(self.leader.shifts.all())
        if not self.employees.exists():
            self.employees.set(self.leader.role.employees.all())
        if self.leader.type in ['O', 'G']:
            if self.shifts.count() > 0:
                self.leader.shifts.clear()
                self.leader.save()
