import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from .basemodels import AutoSlugModel, BaseEmployee




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
    icon_id = models.CharField(max_length=300, null=True, blank=True)

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

    def __str__(self): return f'{self.employee.initials} trained on {self.shift}'


class Employee(BaseEmployee):
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


class Shift(AutoSlugModel):
    verbose_name = models.CharField(max_length=300)
    start_time = models.TimeField()
    hours = models.SmallIntegerField()
    phase = models.ForeignKey(TimePhase, on_delete=models.CASCADE, related_name='shifts')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='shifts')
    class WeekdayChoices(models.TextChoices):
        S = 'S', 'Sun'
        M = 'M', 'Mon'
        T = 'T', 'Tue'
        W = 'W', 'Wed'
        R = 'R', 'Thu'
        F = 'F', 'Fri'
        A = 'A', 'Sat'
    weekdays = models.CharField(max_length=7, choices=WeekdayChoices.choices, default="SMTWRFA")
    on_holidays = models.BooleanField(default=True)

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

class ScheduleQuerySet(models.QuerySet):
    pass

class ScheduleManager(models.Manager):
    pass

class BaseSchedule(models.Model):
    class Meta:
        abstract = True

    objects = ScheduleManager()

    def infer_fields(self):
        if not self.start_date:
            if self.department.schedules.exists():
                self.start_date = self.department.schedules.latest().start_date + datetime.timedelta(days=self.department.schedule_week_length * 7)
            else:
                self.start_date = self.department.get_first_unused_start_date()
        if not self.year:
            if isinstance(self.start_date, str):
                if self.start_date[0:4].isdigit():
                    self.year = int(self.start_date[0:4])
                else:
                    self.year = self.start_date.year
            else:
                self.year = self.start_date.year
        if not self.n:
            self.n = self.department.schedules.filter(year=self.year).count() + 1
        if not self.slug:
            self.slug = slugify(f'sch-{self.year}-{self.n}')

    def save(self, *args, **kwargs):
        created = not self.pk
        self.infer_fields()
        super().save(*args, **kwargs)
        if created:
            self.versions.create(n=1)

class Schedule(BaseSchedule):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schedules')
    start_date = models.DateField()
    year       = models.PositiveSmallIntegerField()
    n          = models.PositiveSmallIntegerField()
    slug       = models.SlugField(max_length=300, unique=True)
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


class Version(models.Model):
    schedule       = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='versions')
    n              = models.PositiveSmallIntegerField()
    status         = models.CharField(max_length=1, choices=Schedule.StatusChoices.choices, default=Schedule.StatusChoices.D)

    def __str__(self): return f'{self.schedule} {self.effective_date}'

    class Meta:
        ordering = ['status','n']

    def save(self, *args, **kwargs):
        created = not self.pk
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
                wd = self.workdays.create(date=sd + datetime.timedelta(days=i), sd_id=i, wk_id=wk_id, pd_id=pd_id,
                                          weekday="SMTWRFA"[i % 7])
                wd.save()

class BaseWorkday(models.Model):
    date = models.DateField()
    weekday = models.CharField(max_length=1, choices=Shift.WeekdayChoices.choices, null=True, blank=True)
    sd_id = models.PositiveSmallIntegerField(null=True, blank=True)
    wk_id = models.PositiveSmallIntegerField(null=True, blank=True)
    pd_id = models.PositiveSmallIntegerField(null=True, blank=True)

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


    def url(self): return reverse('dept:sch:wd:detail', kwargs={
                                                'dept':self.version.schedule.department.slug,
                                                'sch':self.version.schedule.slug,
                                                'ver':self.version.n,
                                                'wd':self.sd_id,})

class Workday(BaseWorkday):
    version  = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='workdays')
    is_holiday = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

class BaseSlot(models.Model):
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='%(class)s')
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='%(class)s')
    class Meta:
        abstract = True

class Slot(BaseSlot):
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name='slots')
    shift   = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='slots')
    class Meta:
        ordering = ['shift']

    def __str__(self): return f'{self.workday} {self.shift}'


class TdoSlot(BaseSlot):
    class Meta:
        ordering = ['pk']

    def __str__(self): return f'{self.workday} {self.pk}'


class PtoSlot(BaseSlot):
    class Meta:
        ordering = ['pk']

    def __str__(self): return f'{self.workday} {self.pk}'


class SlotOption(models.Model):
    slot     = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='options')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='%(class)s')

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

    def __str__(self): return f'{self.department} {self.start_date}'

    class Meta:
        ordering = ['status','employee']

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
            for i in range(sch_days):
                if i < max_ts_day:
                    self.template_slots.create(sd_id=i,
                                               employee=self.employee,
                                               type='G'
                                               ).save()
                else:
                    self.template_slots.create(sd_id=i,
                                               employee=self.employee,
                                               type='G',
                                               following=self.template_slots.get(sd_id=i % max_ts_day)
                                               ).save()







    objects = EmployeeTemplateScheduleManager()


class BaseTemplateSlot(models.Model):
    template_schedule = models.ForeignKey(EmployeeTemplateSchedule, on_delete=models.CASCADE, related_name='template_slots')
    sd_id             = models.PositiveSmallIntegerField()
    employee          = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='template_slots')
    direct_shift      = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='direct_template_slots', null=True, blank=True)
    rotating_shifts   = models.ManyToManyField(Shift, related_name='rotating_template_slots')
    following         = models.ForeignKey('self', on_delete=models.CASCADE, related_name='followers', null=True, blank=True)

    class DTSTypeChoices(models.TextChoices):
        D = 'D', 'Direct'
        R = 'R', 'Rotating'
        G = 'G', 'Generic'
        O = 'O', 'Off'
    type = models.CharField(max_length=1, choices=DTSTypeChoices.choices, default=DTSTypeChoices.D)

    def __str__(self): return f'Template {self.sd_id} {self.employee.initials} {self.type}'

    class Meta:
        ordering = ['template_schedule', 'direct_shift', 'sd_id']

    class DTSTypeColor(models.TextChoices):
        D = 'bg-indigo-700 text-indigo-400'
        R = 'bg-emerald-700 text-emerald-400'
        G = 'bg-sky-700 text-sky-400'
        O = 'bg-rose-700 text-rose-400'

    def type_color(self): return self.DTSTypeColor[self.type]

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        try:
            if self.direct_shift:
                weekday_id = "SMTWRFA"[self.sd_id % 7]

                if weekday_id in self.direct_shift.weekdays:
                    pass
        except ValueError(f'{self.direct_shift} does not have {self.sd_id} as a weekday'):
            self.direct_shift = None
            self.save()








