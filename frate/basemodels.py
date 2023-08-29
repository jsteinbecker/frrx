import datetime

from computedfields.models import ComputedFieldsModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


from django.urls import reverse
from django.utils.text import slugify


class Weekday(models.Model):
    abvr = models.CharField(max_length=1, primary_key=True)
    short = models.CharField(max_length=3)
    name = models.CharField(max_length=10)
    n = models.SmallIntegerField()

    def __str__(self): return self.short

    class Meta:
        ordering = ['n']

    def sd_ids(self):
        return [(7 * i) + self.n for i in range(10)]


class AutoSlugModel(models.Model):
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70, unique=True, primary_key=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save()

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._state.adding = False
        instance._state.db = db
        instance._old_values = dict(zip(field_names, values))
        return instance

    def data_changed(self, fields):
        if hasattr(self, '_old_values'):
            if not self.pk or not self._old_values:
                return True

            for field in fields:
                if getattr(self, field) != self._old_values[field]:
                    return True
            return False

        return True


class BaseEmployee(AutoSlugModel):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.first_name:
            self.first_name = self.name.split()[0]
        if not self.last_name:
            self.last_name = self.name.split()[-1]
        if not self.initials:
            initials = self.first_name[0] + self.last_name[0]
            if self.department.employees.filter(initials=initials).exists():
                initials += str(self.department.employees.filter(initials__startswith=initials).count() + 1)
            self.initials = initials
        super().save()

    @property
    def direct_template_slots(self):
        return self.template_slots.filter(type='D')

    @property
    def rotating_template_slots(self):
        return self.template_slots.filter(type='R')

    @property
    def available_template_slots(self):
        return self.template_slots.filter(type='A')

    @property
    def id_tuple(self):
        return self.department.slug, self.slug


class EmployeeTemplateSetBuilderMixin(models.Model):
    class Meta:
        abstract = True

    def check_template_quantity(self):
        if self.template_week_count * 7 != self.template_schedule.template_slots \
                .filter(following__isnull=True).count():
            raise ValueError('Template week count does not match template schedule length.')
        if self.template_schedule.latest().template_slots.count() != self.department.schedule_week_length * 7:
            raise ValueError('Template schedule length does not match department schedule length.')
        return

    def build_template_set(self):
        try:
            self.check_template_quantity()
        except ValueError as e:
            ts = self.template_schedules.create(active=True)
            ts.save()

            ts_range = self.versions.latest().workdays.count() // self.template_week_count
            for i in range(self.versions.latest().workdays.count()):
                tss = ts.template_slots.create(
                    employee=self,
                    sd_id=i,
                    type='G',
                )
                if i >= ts_range:
                    tss.following = ts.template_slots.filter(sd_id=i % ts_range, employee=self).first()
                tss.save()
            ts.save()
        return self.template_schedules.latest()


class BaseSchedule(models.Model):
    class Meta:
        abstract = True

    @property
    def start_datetime(self):
        return datetime.datetime.combine(self.start_date, datetime.time())

    def _infer_fields(self):
        if not self.start_date:
            if self.department.schedules.exists():
                self.start_date = self.department.schedules.last().start_date \
                                  + datetime.timedelta(days=self.department.schedule_week_length * 7)
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
        if self.pk:
            if self.versions.exists():
                self.percent = max(list(self.versions.values_list('percent', flat=True)))

    def _gather_template_slots(self):
        from .models import BaseTemplateSlot

        self.template_slots.set(
            BaseTemplateSlot.objects.filter(employee__in=self.employees.all(),
                                            template_schedule__status='A')
        )

    def save(self, *args, **kwargs):
        self._infer_fields()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('dept:sch:detail', kwargs={'dept': self.department.slug, 'sch': self.slug})

    @property
    def url(self):
        return self.get_absolute_url()


class BaseWorkday(ComputedFieldsModel):
    date = models.DateField()
    weekday = models.ForeignKey('Weekday', on_delete=models.PROTECT, null=True, blank=True)
    sd_id = models.PositiveSmallIntegerField(null=True, blank=True)
    wk_id = models.PositiveSmallIntegerField(null=True, blank=True)
    pd_id = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['date']

    def __str__(self):
        return f'v{self.version.n}[{self.date}]'

    def save(self, *args, **kwargs):
        if not self.weekday:
            self.weekday = Weekday.objects.get(n=int(self.date.strftime('%w')))

        super().save(*args, **kwargs)

        for pto_slot in self.pto_slots.all():
            pto_slot.save()

    @property
    def employees(self):
        from frate.empl.models import Employee
        return Employee.objects.filter(pk__in=self.slots.filter(employee__isnull=False) \
                                       .values_list('employee__pk', flat=True))

    def assign_direct_template(self):
        """
        ASSIGNS DIRECT TEMPLATES TO SLOTS ON WORKDAY
        """
        for slot in self.slots.filter(direct_template__isnull=False, employee__isnull=True).order_by('?'):
            slot.set_employee(slot.direct_template, 'M')
            slot.save()

    def assign_rotating_templates(self):
        """
        ASSIGNS ROTATING TEMPLATES TO SLOTS ON WORKDAY
        """
        # Rotating Templates with No Assignment
        for slot in self.slots.filter(rotating_templates__isnull=False, employee__isnull=True):
            options = slot.rotating_templates \
                .exclude(pk__in=self.slots.filter(employee__isnull=False) \
                         .values_list('employee__pk', flat=True))
            if slot.adjacent_rotating_template_slot:
                if slot.adjacent_rotating_template_slot.employee:
                    options = options.filter(pk=slot.adjacent_rotating_template_slot.employee.pk)
            else:
                options = slot.rotating_templates \
                    .exclude(pk__in=self.slots.filter(employee__isnull=False) \
                             .values_list('employee__pk', flat=True))
            if options:
                slot.set_employee(options.order_by('?').first(), 'M')
                slot.save()

    def get_who_needs_assignment(self):
        from frate.empl.models import Employee
        has_d_template = Employee.objects.filter(pk__in=self.slots.filter(
            direct_template__isnull=False).values('direct_template__pk'))
        has_r_template = Employee.objects.filter(pk__in=self.slots.filter(
            rotating_templates__isnull=False).values('rotating_templates__pk'))
        has_template = has_d_template | has_r_template
        return has_template.exclude(pk__in=self.pto_requests.values('employee__pk')) \
            .exclude(pk__in=self.slots.filter(employee__isnull=False).values('employee__pk'))

    def get_employee_details(self, empl):
        from frate.empl.models import Employee
        if isinstance(empl, str):
            employee = Employee.objects.get(slug=empl)
        elif isinstance(empl, Employee):
            employee = empl
        else:
            raise TypeError(f'empl must be str or Employee, not {type(empl)}')
        # DETAILS
        details = {}
        details['date'] = self.date
        details['template'] = employee.role_slots.filter(sd_id=self.sd_id).first() or None
        details['pto'] = employee.pto_requests.filter(date=self.date).first() or None
        details['slot'] = self.slots.filter(employee=employee).first() or None
        details['workday'] = self

        return details

    @property
    def url(self):
        return reverse('dept:sch:ver:wd:detail', kwargs={
            'dept': self.version.schedule.department.slug,
            'sch': self.version.schedule.slug,
            'ver': self.version.n,
            'wd': self.sd_id, })

    @property
    def as_args(self):
        return ([self.version.schedule.department.slug,
                 self.version.schedule.slug,
                 self.version.n,
                 self.sd_id])


