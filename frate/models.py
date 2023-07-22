import datetime

from computedfields.models import computed, ComputedFieldsModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.text import slugify
from .basemodels import AutoSlugModel, BaseEmployee, BaseSchedule, EmployeeTemplateSetBuilderMixin, BaseWorkday, Weekday
from frate.slot.models import Slot
from .empl.models import Employee
from .payprd.models import PayPeriod
from .sft.models import Shift
from .ver.models import Version
from .wday.models import Workday


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
    image = models.FilePathField(max_length=500,path='static/media/',null=True,blank=True)
    pto_max_week_window = models.PositiveSmallIntegerField(default=52,
                                help_text='Maximum number of weeks in the future that PTO can be requested')

    def __str__(self): return self.name

    def get_first_unused_start_date(self):
        start_date = self.initial_start_date
        while self.schedules.filter(start_date=start_date).exists():
            start_date += datetime.timedelta(days=self.schedule_week_length * 7)
        return start_date

    @property
    def url(self):
        return reverse('dept:detail', kwargs={'dept': self.slug})


class ShiftTraining(models.Model):
    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    effective_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    rank = models.PositiveSmallIntegerField(default=0)

    def __str__(self): return f'{self.employee.initials}:{self.shift} Training'

    class Meta:
        ordering = ['rank']
        verbose_name = 'Shift Training'
        verbose_name_plural = 'Shift Trainings'


class Schedule(BaseSchedule):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schedules')
    start_date = models.DateField()
    year    = models.PositiveSmallIntegerField()
    n       = models.PositiveSmallIntegerField()
    slug    = models.SlugField(max_length=300)
    percent = models.IntegerField(default=0)
    employees = models.ManyToManyField(Employee, related_name='schedules')
    shifts    = models.ManyToManyField(Shift, related_name='schedules')

    class StatusChoices(models.TextChoices):
        D = 'D', 'Draft'
        P = 'P', 'Published'
        A = 'A', 'Archived'
    status = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.D)

    def __str__(self): return f'{self.department} {self.start_date}'

    class Meta:
        ordering = ['start_date']
        unique_together = ['department', 'year', 'n'], ['department', 'slug']


class PtoRequest(models.Model):
    """
    A request for Paid Time Off. PtoRequests exist outside the workdays of versions. They instead
    are translated into PtoSlots, which occupy a relationship with the actual workday objects.
    """
    date        = models.DateField()
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_requests')
    class StatusChoices(models.TextChoices):
        PENDING  = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        DENIED   = 'D', 'Denied'
    status      = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    class Meta:
        ordering = ['date']
        unique_together = ['date', 'employee']

    def __str__(self): return f'{self.employee.initials}|{self.date}'

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
        workdays = Workday.objects.filter(
            version__schedule__employees=self.employee,
            date=self.date
        )
        for wd in workdays:
            if wd is not None:
                if not wd.slots.filter(employee=self.employee).exists():
                    if not PtoSlot.objects.filter(employee=self.employee, workday=wd).exists():
                        ptoslot = PtoSlot.objects.create(
                                employee=self.employee,
                                workday=wd,
                                hours=self.employee.pto_hours,
                                request=self
                            )
                        ptoslot.save()

    def _ensure_no_conflicts_in_approved_status(self):
        if self.status == 'A':
            if self.employee.pto_requests.filter(date=self.date, status='A').exists():
                raise ValidationError('Employee already has an approved PTO request for this date')


class PtoSlot(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_slots')
    workday  = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='pto_slots')
    hours    = models.IntegerField(default=8)
    request  = models.ForeignKey(PtoRequest,on_delete=models.CASCADE, related_name='pto_slots')
    period   = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='pto_slots', null=True, blank=True)

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


class SlotOption(ComputedFieldsModel):

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='options')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='options')

    @computed(models.BooleanField(default=False))
    def has_pto_block(self):
        return self.slot.workday.on_pto.filter(slug=self.employee.slug).exists()
    @computed(models.BooleanField(default=False))
    def has_tdo_block(self):
        return self.slot.workday.on_tdo.filter(slug=self.employee.slug).exists()
    @computed(models.BooleanField(default=False))
    def has_same_day_block(self):
        return self.slot.workday.slots.exclude(shift=self.slot.shift).filter(employee=self.employee).exists()
    @computed(models.BooleanField(default=False))
    def has_prev_turnaround_block(self):
        return self.slot.workday.slots.filter(shift__phase__rank__gt=self.slot.shift.phase.rank, employee=self.employee).exists()
    @computed(models.BooleanField(default=False))
    def has_next_turnaround_block(self):
        return self.slot.workday.slots.filter(shift__phase__rank__lt=self.slot.shift.phase.rank, employee=self.employee).exists()
    @computed(models.BooleanField(default=False))
    def has_block(self):
        return self.has_pto_block or self.has_tdo_block or self.has_same_day_block or self.has_prev_turnaround_block or self.has_next_turnaround_block

    @computed(models.IntegerField(null=True, blank=True))
    def period_hours(self):
        if self.slot.version.periods.filter(employee=self.employee).exists():
            return self.slot.version.periods.get(employee=self.employee,pd_id=self.slot.workday.pd_id).hours
        else:
            return 0

    @computed(models.IntegerField(null=True, blank=True))
    def week_hours(self):
        if self.employee:
            hours = self.slot.workday.version.slots.filter(employee=self.employee,
                                                           workday__wk_id=self.slot.workday.wk_id)\
                                                    .aggregate(hours=Sum('shift__hours'))['hours']
            if hours:
                return hours
        else:
            return 0

    class Meta:
        ordering = ['slot', 'employee']

    def __str__(self):
        return f'{self.slot}-OPT::{self.employee.initials}'


        super().save(*args, **kwargs)

    def clean(self):
        if self.slot.workday.pto_requests.filter(employee=self.employee).exists():
            self.delete()
            print('SlotOption cleared via PTO Request')
        super().clean()


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


class Role(models.Model):
    week_count = models.PositiveSmallIntegerField(default=2)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    max_employees = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    employees = models.ManyToManyField(Employee, related_name='roles')
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    class TemplateTypeChoices(models.TextChoices):
        GENERIC = 'G', 'Generic'
        OFF = 'O', 'Off'
        DIRECT = 'D', 'Direct'
        ROTATING = 'R', 'Rotating'

    @property
    def url(self):
        return reverse('dept:role:detail', kwargs={'dept': self.department.slug, 'role': self.slug})

    @property
    def slots(self):
        return RoleSlot.objects.filter(leader__role=self)

    def available_employees(self):
        shifts = self.slots.values('shifts').distinct()
        return self.department.employees.filter(shifts__in=shifts)

    def validate_week_count(self):
        if self.department.schedule_week_length % self.week_count != 0:
            raise ValueError('Template week count must be a factor of the schedule week length')
        return

    def validate_max_employees(self):
        if self.leader_slots.filter(type='D').exists():
            if self.max_employees and self.max_employees > self.cycles_per_schedule():
                raise ValueError('Template max employees must be less than or equal to the department max employees')
        return

    def construct_scheme(self):
        for i in range(self.week_count * 7):
            ls = self.leader_slots.create(sd_id=i + 1)
            ls.save()

    def cycles_per_schedule(self):
        return self.department.schedule_week_length // self.week_count

    def __str__(self):
        return f'{self.department} {self.name}'

    def save(self, *args, **kwargs):
        created = not self.pk
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.max_employees:
            self.max_employees = self.cycles_per_schedule()
        super().save(*args, **kwargs)
        if not self.leader_slots.exists():
            self.construct_scheme()


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
        n_cycles     = self.role.cycles_per_schedule()
        cycle_length = self.role.week_count * 7

        for i in range(n_cycles):
            s = self.slots.create(sd_id=self.sd_id + (i * cycle_length), type=self.type)
            s.save()

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if not self.slots.exists():
            self._construct_slots()
        else:
            for slot in self.slots.all():
                if slot.type != self.type:
                    slot.type = self.type
                    slot.save()
        if self.type in ['O','G']:
            self.shifts.clear()
            for slot in self.slots.all():
                if slot.shifts.count() > 0:
                    slot.shifts.clear()


class RoleSlot(models.Model):
    leader  = models.ForeignKey(RoleLeaderSlot, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    sd_id   = models.PositiveSmallIntegerField()
    type    = models.CharField(max_length=1,
                                choices=Role.TemplateTypeChoices.choices,
                                default=Role.TemplateTypeChoices.GENERIC)
    shifts      = models.ManyToManyField(Shift, related_name='role_slots')
    employees   = models.ManyToManyField(Employee, related_name='role_slots')

    class Meta:
        ordering = ['sd_id']

    def __str__(self): return f'RoleSlot|{self.sd_id}{self.type}|'

    def unassigned_shifts(self):
        weekday     = Weekday.objects.get(n=(self.sd_id - 1) % 7)
        shifts      = weekday.shifts.filter(department=self.leader.role.department)
        assigned    = shifts.filter(role_slots__sd_id=self.sd_id, role_slots__type=self.type).values('pk')
        return shifts.exclude(pk__in=assigned)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if not self.shifts.exists():
            self.shifts.set(self.leader.shifts.all())
        if not self.employees.exists():
            self.employees.set(self.leader.role.employees.all())
        if self.type in ['O','G']:
            if self.shifts.count() > 0:
                self.leader.shifts.clear()
                self.leader.save()

