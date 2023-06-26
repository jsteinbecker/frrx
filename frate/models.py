import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import OuterRef, F
from django.urls import reverse
from django.utils.text import slugify
from .basemodels import AutoSlugModel, BaseEmployee, BaseSchedule, EmployeeTemplateSetBuilderMixin, BaseWorkday, Weekday
from django import forms
from .managers import ShiftSlotManager, SlotQuerySet, TdoSlotManager, PtoSlotManager
from .validators import RoleEmployeeValidator, SlotOvertimeValidator


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

    def __str__(self): return self.name

    def get_first_unused_start_date(self):
        start_date = self.initial_start_date
        while self.schedules.filter(start_date=start_date).exists():
            start_date += datetime.timedelta(days=self.schedule_week_length * 7)
        return start_date


class ShiftTraining(models.Model):
    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    effective_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    rank = models.PositiveSmallIntegerField(default=0)

    def __str__(self): return f'{self.employee.initials} trained on {self.shift}'

    class Meta:
        ordering = ['rank']
        verbose_name = 'Shift Training'
        verbose_name_plural = 'Shift Trainings'


class EmployeeTrainingMixin(models.Model):
    class Meta:
        abstract = True

    def available_shifts(self):
        return Shift.objects.filter(
            pk__in=self.shifttraining_set.filter(is_active=True).values_list('shift__pk', flat=True)
        )

    def unavailable_shifts(self):
        return Shift.objects.filter(
            pk__in=self.shifttraining_set.filter(is_active=False).values_list('shift__pk', flat=True)
        )

    def untrained_shifts(self):
        return self.department.shifts.exclude(
            pk__in=self.shifttraining_set.values_list('shift__pk', flat=True)
        )


class Employee(BaseEmployee, EmployeeTemplateSetBuilderMixin, EmployeeTrainingMixin):
    first_name = models.CharField(max_length=70)
    last_name  = models.CharField(max_length=70)
    initials   = models.CharField(max_length=10)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    shifts     = models.ManyToManyField('Shift', related_name='employees', through=ShiftTraining)
    icon_id    = models.CharField(max_length=300, null=True, blank=True)
    start_date = models.DateField(default='2023-02-05')
    is_active  = models.BooleanField(default=True)
    fte        = models.FloatField(default=1.0, validators=[MaxValueValidator(1.0), MinValueValidator(0.0)])
    pto_hours  = models.SmallIntegerField(default=0)
    template_week_count = models.PositiveSmallIntegerField(default=2)
    phase_pref = models.ForeignKey(TimePhase, to_field='slug',
                                   on_delete=models.CASCADE,
                                   related_name='employees', null=True, blank=True)
    streak_pref = models.PositiveSmallIntegerField(default=3)

    def __str__(self): return self.name

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def url(self):
        return reverse('dept:empl:detail', args=[self.department.slug, self.slug])

    @property
    def fte_prd(self):
        return int(self.fte * 80)


class Shift(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)
    start_time   = models.TimeField()
    hours = models.SmallIntegerField(default=10)
    phase = models.ForeignKey(TimePhase, to_field='slug', on_delete=models.CASCADE,
                              related_name='shifts', null=True, blank=True)
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='shifts')
    is_active   = models.BooleanField(default=True)
    weekdays    = models.ManyToManyField(Weekday, related_name='shifts')
    on_holidays = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time', 'name']

    def __str__(self):
        return self.name

    class Auto:
        @staticmethod
        def set_phase(instance):
            if instance.phase is None:
                instance.phase = instance.department.organization.phases.filter(
                    end_time__gte=instance.start_time).first()

        @staticmethod
        def set_weekdays(instance):
            if not instance.weekdays.exists():
                instance.weekdays.set(Weekday.objects.all())

        @staticmethod
        def set_slug(instance):
            if not instance.slug:
                instance.slug = f'{instance.name.lower().replace(" ", "-")}-{instance.department.slug}'

    auto = Auto()

    def save(self, *args, **kwargs):
        created = not self.pk
        self.auto.set_slug(self)
        self.auto.set_phase(self)
        self.auto.set_weekdays(self)
        super().save(*args, **kwargs)

    def clean(self):
        if self.weekdays == '':
            raise ValidationError('Weekdays must be specified')
        if self.hours == 0:
            raise ValidationError('Shift hours must be greater than 0')

    def get_absolute_url(self):
        return reverse('dept:sft:detail', args=[self.department.slug, self.slug])

    @property
    def url(self):
        return self.get_absolute_url()


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


class Version(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='versions')
    n = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=Schedule.StatusChoices.choices, default=Schedule.StatusChoices.D)
    percent = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.schedule}:V{self.n}'

    class Meta:
        ordering = ['n', 'status']

    def save(self, *args, **kwargs):
        created = not self.pk

        if not created:
            if self.slots.count() > 0:
                self._update_percent()

        super().save(*args, **kwargs)

        if created:
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

    def _update_percent(self):
        self.percent = int((self.slots.filter(employee__isnull=False).count() / self.slots.count()) * 100)

    @property
    def url(self):
        return reverse('dept:sch:ver:detail', kwargs={
            'dept': self.schedule.department.slug,
            'sch': self.schedule.slug,
            'ver': self.n, })

    def assign_positive_templates(self):
        for wd in Workday.objects.filter(pk__in=self.slots.filter(direct_template__isnull=False) \
                .values('workday').distinct()):
            wd.assign_direct_template()
        for wd in Workday.objects.filter(pk__in=self.slots.filter(rotating_templates__isnull=False) \
                .values('workday').distinct()):
            wd.assign_rotating_templates()

    def solve(self):
        self.assign_positive_templates()
        for slot in self.slots.filter(employee__isnull=True):
            slot.solve()


class Workday(BaseWorkday):
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='workdays')
    is_holiday = models.BooleanField(default=False)
    templated_off = models.ManyToManyField(Employee, related_name='templated_off_days', blank=True)
    on_pto = models.ManyToManyField(Employee, related_name='pto_days', blank=True)

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
        return SlotOption.objects.filter(pk__in=self.slots.values('options__pk'))

    @property
    def pto_requests(self) -> 'QuerySet[PtoRequest]':
        return PtoRequest.objects.filter(date=self.date)

    @property
    def on_tdo(self) -> 'QuerySet[Employee]':
        return Employee.objects.filter(slug__in=RoleSlot.objects.filter(sd_id=self.sd_id,
                                            type='O')\
                                            .values('leader__role__employees')\
                                            .distinct())


class Slot(models.Model):
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='slots')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, related_name='slots', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='slots', null=True, blank=True,
                                 validators=[SlotOvertimeValidator],
                                 limit_choices_to={'is_active':True})

    class SlotTypeChoices(models.TextChoices):
        SHIFT = 'S', 'Shift'
        TDO = 'T', 'Templated Day Off'
        PTO = 'P', 'Paid Time Off'

    slot_type = models.CharField(max_length=1, choices=SlotTypeChoices.choices, default=SlotTypeChoices.SHIFT)
    direct_template = models.ForeignKey('Employee', on_delete=models.SET_NULL, related_name='direct_template_for',
                                        null=True, blank=True)
    rotating_templates = models.ManyToManyField('Employee', related_name='rotating_template_for', blank=True)
    generic_templates = models.ManyToManyField('Employee', related_name='generic_template_for', blank=True)
    class FilledByChoices(models.TextChoices):
        USER= 'U', 'User'
        MODEL= 'M', 'Model'
    filled_by = models.CharField(max_length=1, choices=FilledByChoices.choices,
                                 default=FilledByChoices.USER, null=True, blank=True)

    class Meta:
        ordering = ['shift__start_time', 'workday__date']
        unique_together = ['workday', 'shift'], ['workday', 'employee']

    def __str__(self):
        return f'{self.workday} {self.shift}'

    @property
    def url(self):
        return reverse('dept:sch:ver:wd:slot:detail', kwargs={
            'dept': self.workday.version.schedule.department.slug,
            'sch': self.workday.version.schedule.slug,
            'ver': self.workday.version.n,
            'wd': self.workday.sd_id,
            'sft': self.shift.slug,
        })

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        self._build_options()
        self._check_slot_type_valid()
        try:
            self._check_pto_requests()
        except ValidationError:
            employee = self.employee
            self.employee = None
            self.save()
            print(f'{employee} is on PTO: {self} automatically cleared employee')

    def _check_pto_requests(self):
        if self.workday.pto_requests.filter(employee=self.employee).exists():
            raise ValidationError('Employee is on PTO')

    def _build_options(self):
        pto = self.workday.pto_requests.values('employee')
        d_template = RoleSlot.objects.filter(shifts=self.shift,
                                             sd_id=self.workday.sd_id,
                                             type='D')
        r_template = RoleSlot.objects.filter(shifts=self.shift,
                                              sd_id=self.workday.sd_id,
                                              type='R')
        g_template = RoleSlot.objects.filter(sd_id=self.workday.sd_id,
                                              type='G')
        if d_template.exists():
            self.direct_template = d_template.first().leader.role.employees.exclude(pk__in=pto).first()
        if r_template.exists():
            self.rotating_templates.set(r_template.first().leader.role.employees.exclude(pk__in=pto))
        if g_template.exists():
            self.generic_templates.set(g_template.first().leader.role.employees.exclude(pk__in=pto))

    def _check_slot_type_valid(self):
        if self.slot_type == 'S' and self.shift is None:
            raise ValidationError('Shift must be selected for Shift slot type')
        if self.slot_type == 'T' and self.shift is not None:
            raise ValidationError('Shift must not be selected for Templated Day Off slot type')
        if self.slot_type == 'P' and self.shift is not None:
            raise ValidationError('Shift must not be selected for Paid Time Off slot type')
        if self.slot_type == 'P' and self.employee is None:
            raise ValidationError('Employee must be selected for Paid Time Off slot type')
        if self.slot_type == 'T' and self.employee is None:
            raise ValidationError('Employee must be selected for Templated Day Off slot type')

    def clean(self):
        self._check_slot_type_valid()
        super().clean()

    def _get_role_employees(self):
        role_slot = RoleSlot.objects.filter(shifts=self.shift, sd_id=self.workday.sd_id)
        if role_slot.exists():
            return role_slot.first().leader.role.employees.all()
        else:
            role_slots = RoleSlot.objects.filter(type='G', sd_id=self.workday.sd_id).values('leader__role__employees')
            return Employee.objects.filter(pk__in=role_slots)

    def set_employee(self, employee):
        if employee.shifts.filter(pk=self.shift.pk).exists():
            self.employee = employee
            self.save()
            return True, self
        return False, self

    def conflict_blockers(self) -> 'QuerySet[Employee]':
        if self.workday.get_next():
            next_day = self.workday.get_next().slots.filter(shift__phase__rank__lt=self.shift.phase.rank, )
        else:
            next_day = Slot.objects.none()

        if self.workday.get_prev():
            prev_day = self.workday.get_prev().slots.filter(shift__phase__rank__gt=self.shift.phase.rank, )
        else:
            prev_day = Slot.objects.none()

        on_day = self.workday.slots.exclude(pk=self.pk)

        conflict_risks = next_day | prev_day | on_day
        return Employee.objects.filter(pk__in=conflict_risks.values_list('employee', flat=True))

    def fte_blockers(self):
        out = []
        for empl in self.version.schedule.employees.all():
            prd_hours = sum(list(self.workday.version.slots.filter(employee=empl,
                                                                   workday__pd_id=self.workday.pd_id).values_list(
                'shift__hours', flat=True)))
            if prd_hours + self.shift.hours > empl.fte * 80:
                out.append(empl.pk)
        return Employee.objects.filter(pk__in=out)

    def solve(self):
        trained = Employee.objects.filter(pk__in=self.shift.employees.values_list('pk', flat=True))
        available = trained.exclude(pk__in=self.conflict_blockers().values_list('pk', flat=True)).order_by('?')
        at_fte = self.fte_blockers()
        available = available.exclude(pk__in=at_fte.values_list('pk', flat=True)).order_by('?')
        if available.exists():
            self.set_employee(available.first())

    objects = ShiftSlotManager()
    pto_slots = PtoSlotManager()
    tdo_slots = TdoSlotManager()


class PtoRequest(models.Model):
    """
    A request for Paid Time Off
    """

    date = models.DateField()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_requests')

    class StatusChoices(models.TextChoices):
        PENDING = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        DENIED = 'D', 'Denied'

    status = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    class Meta:
        ordering = ['date']

    def __str__(self): return f'{self.employee} PTOR:{self.date}'


class SlotOptionQuerySet(models.QuerySet):
    pass


class SlotOptionManager(models.Manager):

    def get_queryset(self):
        return SlotOptionQuerySet(self.model, using=self._db)


class SlotOption(models.Model):
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='options')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='%(class)s')

    class LevelChoices(models.TextChoices):
        ASSERTIVE = 'A', 'Assertive'
        PREFERRED = 'P', 'Preferred'
        DEFERENT = 'D', 'Deferent'
        SWAP_IN = 'S', 'Swap In'

    level = models.CharField(max_length=1, choices=LevelChoices.choices, default=LevelChoices.PREFERRED)

    class Meta:
        ordering = ['slot', 'employee']

    def __str__(self):
        return f'{self.slot}-OPT::{self.employee.initials}'

    def save(self, *args, **kwargs):

        def other_slot_options_defer_to_instance():

            if self.slot.workday.options.filter(employee=self.employee).count() == 1:
                self.slot.workday.options.filter(slot__shift=self.slot.shift).exclude(employee=self.employee) \
                    .update(level=self.LevelChoices.DEFERENT)
                self.level = self.LevelChoices.ASSERTIVE
            if self.slot.options.filter(level=self.LevelChoices.ASSERTIVE, employee=self.employee).exists():
                self.level = self.LevelChoices.ASSERTIVE
                for option in self.slot.options.exclude(employee=self.employee).exclude(
                        level=self.LevelChoices.SWAP_IN):
                    option.level = self.LevelChoices.DEFERENT
                    option.save()

        def defer_to_other_direct_templates():
            if self.slot.options.filter(level=self.LevelChoices.ASSERTIVE).exclude(employee=self.employee).exists():
                self.level = self.LevelChoices.DEFERENT

        created = not self.pk
        if not created:
            other_slot_options_defer_to_instance()
            defer_to_other_direct_templates()

        super().save(*args, **kwargs)

    def clean(self):
        if self.slot.workday.pto_requests.filter(employee=self.employee).exists():
            self.delete()
            print('SlotOption cleared via PTO Request')
        if self.slot.employee == self.slot.direct_template and self.employee != self.slot.direct_template:
            self.delete()
        super().clean()

    objects = SlotOptionManager()


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
    slug = models.SlugField(max_length=100)
    max_employees = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    employees = models.ManyToManyField(Employee, related_name='roles',
                                       validators=[RoleEmployeeValidator])
    active = models.BooleanField(default=True)

    class TemplateTypeChoices(models.TextChoices):
        GENERIC = 'G', 'Generic'
        OFF = 'O', 'Off'
        DIRECT = 'D', 'Direct'
        ROTATING = 'R', 'Rotating'



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
        weekday = Weekday.objects.get(n=(self.sd_id) % 7)
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
    leader = models.ForeignKey(RoleLeaderSlot, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    sd_id = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=1,
                            choices=Role.TemplateTypeChoices.choices,
                            default=Role.TemplateTypeChoices.GENERIC)
    shifts = models.ManyToManyField(Shift, related_name='role_slots')
    employees = models.ManyToManyField(Employee, related_name='role_slots')

    class Meta:
        ordering = ['sd_id']

    def __str__(self): return f'RoleSlot|{self.sd_id}{self.type}|'

    def unassigned_shifts(self):
        weekday = Weekday.objects.get(n=(self.sd_id - 1) % 7)
        shifts = weekday.shifts.filter(department=self.leader.role.department)
        assigned = shifts.filter(role_slots__sd_id=self.sd_id, role_slots__type=self.type).values('pk')
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

