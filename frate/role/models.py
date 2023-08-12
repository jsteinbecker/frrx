from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from frate.empl.models import Employee


class RoleQuerySet(models.QuerySet):
    def select_slots(self):
        from frate.models import RoleSlot
        return RoleSlot.objects.filter(pk__in=self.select_related('leader_slots__slots').values('leader_slots__slots__pk'))


class RoleManager(models.Manager):
    def get_queryset(self):
        return RoleQuerySet(self.model, using=self._db)

    def select_slots(self):
        return self.get_queryset().select_slots()


class Role(models.Model):
    """
    A Role is a template for a set of RoleSlots. It is used to create a schedule.
    It can be assigned to one or more employees.

    fields:
        - week_count: the number of weeks in the template
        - department: the department the template belongs to
        - name: the name of the template
        - slug: the slug of the template
        - max_employees: the maximum number of employees that can be assigned to the template
        - employees: the employees assigned to the template
        - active: whether the template is active
        - description: a description of the template

    """
    week_count = models.PositiveSmallIntegerField(default=2)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    max_employees = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    employees     = models.ManyToManyField(Employee, related_name='roles')
    active        = models.BooleanField(default=True)
    description   = models.TextField(blank=True, null=True)

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
        from frate.models import RoleSlot
        return RoleSlot.objects.filter(leader__role=self)

    @property
    def shifts(self):
        return self.leader_slots.values('shifts__pk').distinct()

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

    objects = RoleManager()