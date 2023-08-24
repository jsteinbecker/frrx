from django.db import models

from frate.basemodels import BaseSchedule
from frate.empl.models import Employee
from frate.sft.models import Shift


class Schedule(BaseSchedule):
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='schedules')
    start_date = models.DateField()
    year = models.PositiveSmallIntegerField()
    n = models.PositiveSmallIntegerField()
    slug = models.SlugField(max_length=300)
    percent = models.IntegerField(default=0)
    employees = models.ManyToManyField(Employee, related_name='schedules')
    shifts = models.ManyToManyField(Shift, related_name='schedules')
    roles = models.ManyToManyField('Role', related_name='schedules')

    class StatusChoices(models.TextChoices):
        DRAFT = 'D', 'Draft'
        PUBLISHED = 'P', 'Published'
        ARCHIVED = 'A', 'Archived'

    status = models.CharField(max_length=1, choices=StatusChoices.choices, default=StatusChoices.DRAFT)

    def is_deletable(self, by_user):
        if not by_user.is_staff: return False
        if self.status == self.StatusChoices.PUBLISHED: return False
        return True

    def __str__(self): return f'{self.department} {self.start_date}'

    class Meta:
        ordering = ['start_date']
        unique_together = ['department', 'year', 'n'], ['department', 'slug']


class HoursOverride(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='employee_hours_overrides')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='hours_overrides')
    hours = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self): return f'{self.schedule} {self.employee}'

