import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from .basemodels import AutoSlugModel, BaseEmployee, BaseSchedule, EmployeeTemplateSetBuilderMixin
from django import forms



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
    img_url = models.CharField(max_length=400, null=True, blank=True)
    image = models.ImageField(max_length=300, upload_to='img/', null=True, blank=True)

    def __str__(self): return self.name

    def get_first_unused_start_date(self):
        start_date = self.initial_start_date
        while self.schedules.filter(start_date=start_date).exists():
            start_date += datetime.timedelta(days=self.schedule_week_length * 7)
        return start_date

class ShiftTraining(models.Model):
    shift          = models.ForeignKey('Shift', on_delete=models.CASCADE)
    employee       = models.ForeignKey('Employee', on_delete=models.CASCADE)
    effective_date = models.DateField(auto_now_add=True)
    is_active      = models.BooleanField(default=True)

    def __str__(self): return f'{self.employee.initials} trained on {self.shift}'


class Employee(BaseEmployee, EmployeeTemplateSetBuilderMixin):
    first_name = models.CharField(max_length=70)
    last_name  = models.CharField(max_length=70)
    initials   = models.CharField(max_length=10)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    shifts     = models.ManyToManyField('Shift', related_name='employees', through=ShiftTraining)
    icon_id    = models.CharField(max_length=300, null=True, blank=True)
    start_date          = models.DateField(default='2023-02-05')
    is_active           = models.BooleanField(default=True)
    fte                 = models.FloatField(default=1.0, validators=[MaxValueValidator(1.0), MinValueValidator(0.0)])
    pto_hours           = models.SmallIntegerField(default=0)
    template_week_count = models.PositiveSmallIntegerField(default=2)

    def __str__(self): return self.name

    @property
    def url(self):
        return reverse('dept:empl:detail', args=[self.department.slug, self.slug])


class Shift(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)
    start_time   = models.TimeField()
    hours        = models.SmallIntegerField(default=10)
    phase        = models.ForeignKey(TimePhase, to_field='slug', on_delete=models.CASCADE, related_name='shifts')
    department   = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='shifts')
    is_active    = models.BooleanField(default=True)
    class WeekdayChoices(models.TextChoices):
        S = 'S', 'Sun'
        M = 'M', 'Mon'
        T = 'T', 'Tue'
        W = 'W', 'Wed'
        R = 'R', 'Thu'
        F = 'F', 'Fri'
        A = 'A', 'Sat'
    weekdays    = models.CharField(max_length=7, choices=WeekdayChoices.choices, default="SMTWRFA")
    on_holidays = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']


    def __str__(self): return self.name

    class Auto:
        @staticmethod
        def set_phase(instance):
            instance.phase = instance.department.organization.phases.filter(end_time__gte=instance.start_time).first()

    auto = Auto()

    def save(self, *args, **kwargs):
        created = not self.pk
        if created: self.auto.set_phase(self)
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



class ScheduleQuerySet(models.QuerySet):
    pass

class ScheduleManager(models.Manager):
    pass


class Schedule(BaseSchedule):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schedules')
    start_date = models.DateField()
    year       = models.PositiveSmallIntegerField()
    n          = models.PositiveSmallIntegerField()
    slug       = models.SlugField(max_length=300)
    percent    = models.IntegerField(default=0)
    employees  = models.ManyToManyField(Employee, related_name='schedules')
    shifts     = models.ManyToManyField(Shift, related_name='schedules')
    class StatusChoices(models.TextChoices):
        D = 'D', 'Draft'
        P = 'P', 'Published'
        A = 'A', 'Archived'
    status     = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.D)

    def url(self): return reverse('dept:sch:detail', kwargs={
                                                'dept':self.department.slug,
                                                'sch':self.slug,})

    def __str__(self): return f'{self.department} {self.start_date}'

    class Meta:
        ordering = ['start_date']
        unique_together = ['department','year','n'],['department','slug']


class Version(models.Model):
    schedule       = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='versions')
    n              = models.PositiveSmallIntegerField()
    status         = models.CharField(max_length=1, choices=Schedule.StatusChoices.choices, default=Schedule.StatusChoices.D)
    percent        = models.IntegerField(default=0)

    def __str__(self): return f'{self.schedule}:V{self.n}'

    class Meta:
        ordering = ['n','status']

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
            weekday = sd.strftime('%a')[0]
            for i in range(1,day_count+1):
                wk_id = i // 7
                pd_id = i // 14
                wd = self.workdays.create(date=sd + datetime.timedelta(days=i-1),
                                          sd_id=i,
                                          wk_id=wk_id,
                                          pd_id=pd_id,
                                          weekday="SMTWRFA"[i % 7])
                wd.save()

    def _update_percent(self):
        self.percent = int((self.slots.filter(employee__isnull=False).count()/self.slots.count())*100)

    @property
    def url(self): return reverse('dept:sch:ver', kwargs={
                                                'dept':self.schedule.department.slug,
                                                'sch':self.schedule.slug,
                                                'ver':self.n,})

    def assign_positive_templates(self):
        for wd in Workday.objects.filter(pk__in=self.slots.filter(direct_template__isnull=False) \
                                                                    .values('workday').distinct()):
            wd.assign_direct_template()
        for wd in Workday.objects.filter(pk__in=self.slots.filter(rotating_templates__isnull=False)\
                                                                    .values('workday').distinct()):
            wd.assign_rotating_templates()

class BaseWorkday(models.Model):
    date    = models.DateField()
    weekday = models.CharField(max_length=1, choices=Shift.WeekdayChoices.choices, null=True, blank=True)
    sd_id   = models.PositiveSmallIntegerField(null=True, blank=True)
    wk_id   = models.PositiveSmallIntegerField(null=True, blank=True)
    pd_id   = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['date']

    def __str__(self): return f'v{self.version.n}[{self.date}]'

    def save(self, *args, **kwargs):
        created = not self.pk
        if created:
            self.weekday = self.date.strftime('%a')[0]
        super().save(*args, **kwargs)
        if created:
            for shift in self.version.schedule.department.shifts.filter(weekdays__contains=self.weekday):
                slot = self.slots.create(shift=shift,version=self.version)
                slot.save()


    @property
    def employees(self):
        return Employee.objects.filter(pk__in=self.slots.filter(employee__isnull=False)\
                                                        .values_list('employee__pk',flat=True))

    def assign_direct_template(self):
        """
        ASSIGNS DIRECT TEMPLATES TO SLOTS ON WORKDAY
        """
        for slot in self.slots.filter(direct_template__isnull=False, employee__isnull=True).order_by('?'):
            slot.employee = slot.direct_template
            slot.save()

    def assign_rotating_templates(self):
        """
        ASSIGNS ROTATING TEMPLATES TO SLOTS ON WORKDAY
        """
        for slot in self.slots.filter(rotating_templates__isnull=False, employee__isnull=True).order_by('?'):
            print(slot.rotating_templates.all())
            options = slot.rotating_templates\
                        .exclude(pk__in=self.slots.filter(employee__isnull=False) \
                                                    .values_list('employee__pk',flat=True))
            if options:
                slot.employee = options.order_by('?').first()
                slot.save()
            else:
                print(f'No options for {slot}')

    def get_who_needs_assignment(self):
        has_d_template = Employee.objects.filter(pk__in=self.slots.filter(
                            direct_template__isnull=False).values('direct_template__pk'))
        has_r_template = Employee.objects.filter(pk__in=self.slots.filter(
                            rotating_templates__isnull=False).values('rotating_templates__pk'))
        has_template = has_d_template | has_r_template
        return has_template.exclude(pk__in=self.pto_requests.values('employee__pk'))\
                            .exclude(pk__in=self.slots.filter(employee__isnull=False).values('employee__pk'))


    @property
    def url(self): return reverse('dept:sch:wd:detail', kwargs={
                                                'dept':self.version.schedule.department.slug,
                                                'sch':self.version.schedule.slug,
                                                'ver':self.version.n,
                                                'wd':self.sd_id,})

    def get_next(self):
        if next_wd := self.version.workdays.filter(sd_id__gt=self.sd_id):
            return next_wd.first()

        return Workday.objects.none()

    def get_prev(self):
        if prev_wd := self.version.workdays.filter(sd_id__lt=self.sd_id):
            return prev_wd.last()

        return Workday.objects.none()


class Workday(BaseWorkday):
    version       = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='workdays')
    is_holiday    = models.BooleanField(default=False)
    templated_off = models.ManyToManyField(Employee, related_name='templated_off_days', blank=True)
    on_pto        = models.ManyToManyField(Employee, related_name='pto_days', blank=True)

    class Meta:
        ordering = ['date']

    @property
    def percent(self):
        if self.slots.count() == 0:
            return 0
        return int((self.slots.filter(employee__isnull=False).count()/self.slots.count())*100)

    @property
    def options(self) -> 'QuerySet[SlotOption]':
        return SlotOption.objects.filter(pk__in=self.slots.values('options__pk'))

    @property
    def pto_requests(self) -> 'QuerySet[PtoRequest]':
        return PtoRequest.objects.filter(date=self.date)

    @property
    def on_tdo(self) -> 'QuerySet[Employee]':
        return Employee.objects.filter(pk__in=self.version.schedule.template_slots.filter(type='O',
                                                                                  template_schedule__status='A',
                                                                                  sd_id=self.sd_id).values('employee__pk'))


class SlotQuerySet(models.QuerySet):

    def filled(self):
        return self.exclude(employee=None)

    def unfilled(self):
        return self.filter(employee=None)

    def empty(self):
        return self.filter(employee=None)

class ShiftSlotManager(models.Manager):

    def get_queryset(self):
        return SlotQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        return super().create(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        return super().get_or_create(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        return super().update_or_create(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        return super().bulk_create(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        return super().bulk_update(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        return super().bulk_update_or_create(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def update(self, *args, **kwargs):
        return super().update(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def filter(self, *args, **kwargs):
        return super().filter(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        return super().exclude(slot_type=Slot.SlotTypeChoices.SHIFT, *args, **kwargs)

    def filled(self):
        return self.exclude(employee=None)

    def unfilled(self):
        return self.filter(employee=None)

class PtoSlotManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(slot_type=Slot.SlotTypeChoices.PTO)

    def create(self, *args, **kwargs):
        return super().create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        return super().get_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        return super().update_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        return super().bulk_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        return super().bulk_update(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        return super().bulk_update_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def update(self, *args, **kwargs):
        return super().update(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def filter(self, *args, **kwargs):
        return super().filter(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        return super().exclude(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

class TdoSlotManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(slot_type=Slot.SlotTypeChoices.TDO)

    def create(self, *args, **kwargs):
        return super().create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        return super().get_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        return super().update_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        return super().bulk_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        return super().bulk_update(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        return super().bulk_update_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def update(self, *args, **kwargs):
        return super().update(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def filter(self, *args, **kwargs):
        return super().filter(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        return super().exclude(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

class Slot(models.Model):
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='slots')
    shift   = models.ForeignKey(Shift, on_delete=models.SET_NULL, related_name='slots', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='slots', null=True, blank=True)
    class SlotTypeChoices(models.TextChoices):
        SHIFT = 'S', 'Shift'
        TDO = 'T', 'Templated Day Off'
        PTO = 'P', 'Paid Time Off'
    slot_type = models.CharField(max_length=1, choices=SlotTypeChoices.choices, default=SlotTypeChoices.SHIFT)
    direct_template = models.ForeignKey('Employee', on_delete=models.SET_NULL, related_name='direct_template_for', null=True, blank=True)
    rotating_templates = models.ManyToManyField('Employee', related_name='rotating_template_for', blank=True)
    generic_templates = models.ManyToManyField('Employee', related_name='generic_template_for', blank=True)

    class Meta:
        ordering = ['shift__start_time','workday__date']
        unique_together = ['workday', 'shift'], ['workday', 'employee']

    def __str__(self): return f'{self.workday} {self.shift}'

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        self._build_options()

    def _build_options(self):
        pto = self.workday.pto_requests.values('employee')
        d_template = BaseTemplateSlot.objects.filter(direct_shift=self.shift,
                                                     sd_id=self.workday.sd_id,
                                                     template_schedule__status='A').exclude(employee__in=pto)
        r_templates = BaseTemplateSlot.objects.filter(rotating_shifts=self.shift,
                                                        sd_id=self.workday.sd_id,
                                                        template_schedule__status='A').exclude(employee__in=pto)
        g_templates = BaseTemplateSlot.objects.filter(sd_id=self.workday.sd_id,
                                                      type=BaseTemplateSlot.DTSTypeChoices.GENERIC,
                                                        template_schedule__status='A').exclude(employee__in=pto)
        if d_template.exists():
            self.direct_template = d_template.first().employee
        if r_templates.exists():
            self.rotating_templates.set(r_templates.values_list('employee', flat=True))
        if g_templates.exists():
            self.generic_templates.set(g_templates.values_list('employee', flat=True))


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

    def set_employee(self, employee):
        if employee.shifts.filter(pk=self.shift.pk).exists():
            self.employee = employee
            self.save()
            return True, self
        return False, self

    objects  = ShiftSlotManager()
    pto_slots = PtoSlotManager()
    tdo_slots = TdoSlotManager()

class PtoRequest(models.Model):
    """
    A request for Paid Time Off
    """

    date     = models.DateField()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_requests')
    class StatusChoices(models.TextChoices):
               PENDING  = 'P', 'Pending'
               APPROVED = 'A', 'Approved'
               DENIED   = 'D', 'Denied'
    status   = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    class Meta:
        ordering = ['date']

    def __str__(self): return f'{self.employee} PTOR:{self.date}'

class SlotOptionQuerySet(models.QuerySet):
    pass

class SlotOptionManager(models.Manager):

    def get_queryset(self):
        return SlotOptionQuerySet(self.model, using=self._db)

class SlotOption(models.Model):
    slot     = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='options')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='%(class)s')
    class LevelChoices(models.TextChoices):
               ASSERTIVE = 'A', 'Assertive'
               PREFERRED = 'P', 'Preferred'
               DEFERENT  = 'D', 'Deferent'
               SWAP_IN   = 'S', 'Swap In'
    level    = models.CharField(max_length=1, choices=LevelChoices.choices, default=LevelChoices.PREFERRED)

    class Meta:
        ordering = ['slot','employee']

    def __str__(self): return f'{self.slot}-OPT::{self.employee.initials}'

    def save(self, *args, **kwargs):

        def other_slot_options_defer_to_instance():

            if self.slot.workday.options.filter(employee=self.employee).count() == 1:
                self.slot.workday.options.filter(slot__shift=self.slot.shift).exclude(employee=self.employee)\
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

    def __str__(self): return f'{self.employee} TemplateSchedule:{self.status}'

    class Meta:
        ordering = ['employee','status']

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
                        s = self.template_slots.create(sd_id=i+1,
                                                   employee=self.employee,
                                                   type='G'
                                                   )
                        s.save()
                    else:
                        s = self.template_slots.create(sd_id=i+1,
                                                   employee=self.employee,
                                                   type='G',
                                                   following=self.template_slots.get(sd_id= i % max_ts_day + 1)
                                                   )
                        s.save()

    def display_template_slot_types(self):
        import json
        array = [slot.type for slot in self.template_slots.all()]
        return json.dumps(array)






    objects = EmployeeTemplateScheduleManager()


class BaseTemplateSlot(models.Model):
    template_schedule = models.ForeignKey(EmployeeTemplateSchedule, on_delete=models.CASCADE, related_name='template_slots')
    sd_id             = models.PositiveSmallIntegerField()
    employee          = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='template_slots')
    direct_shift      = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='direct_template_slots', null=True, blank=True)
    rotating_shifts   = models.ManyToManyField(Shift, related_name='rotating_template_slots')
    following         = models.ForeignKey('self', on_delete=models.CASCADE, related_name='followers', null=True, blank=True)
    schedules         = models.ManyToManyField(Schedule, related_name='template_slots')
    class DTSTypeChoices(models.TextChoices):
              DIRECT   = 'D', 'Direct'
              ROTATING = 'R', 'Rotating'
              GENERIC  = 'G', 'Generic'
              OFF      = 'O', 'Templated Off'
    type    = models.CharField(max_length=1, choices=DTSTypeChoices.choices, default=DTSTypeChoices.DIRECT)

    def __str__(self): return f'Template {self.sd_id} {self.employee.initials} {self.type}'

    class Meta:
        ordering = ['sd_id']

    def check_options(self):
        options = []
        for shift in self.employee.shifts.filter(weekdays="SMTWRFA"[self.sd_id % 7]):
            if not BaseTemplateSlot.objects.filter(template_schedule__is_active=True,
                                               sd_id=self.sd_id,
                                               direct_shift=shift.shift)\
                                        .exclude(employee=self.employee).exists():
                options.append(shift.shift)
            if options: return Shift.objects.filter(pk__in=options)
            else: return Shift.objects.none()


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














