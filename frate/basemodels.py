import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify



class AutoSlugModel(models.Model):
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70, unique=True, primary_key=True)

    class Meta:
        abstract = True

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save()


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


class EmployeeTemplateSetBuilderMixin(models.Model):

    class Meta:
        abstract = True

    def check_template_quantity(self):
        if self.template_week_count * 7 != self.template_schedule.template_slots\
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
        if self.pk:
            if self.versions.exists():
                self.percent = max(list(self.versions.values_list('percent', flat=True)))

    def _gather_template_slots(self):
        from .models import BaseTemplateSlot
        self.template_slots.set(BaseTemplateSlot.objects.filter(employee__in=self.employees.all(),
                                                                template_schedule__status='A'))


    def save(self, *args, **kwargs):
        created = not self.pk
        self._infer_fields()
        super().save(*args, **kwargs)
        if created:
            self.versions.create(n=1)
            for e in self.department.employees.filter(is_active=True, start_date__lte=self.start_date):
                self.employees.add(e)
            for s in self.department.shifts.filter(is_active=True):
                self.shifts.add(s)
            self._gather_template_slots()
