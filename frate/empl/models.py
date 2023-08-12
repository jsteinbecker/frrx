from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from frate.basemodels import BaseEmployee, EmployeeTemplateSetBuilderMixin


class EmployeeQuerySet(models.QuerySet):
    def trained_for(self, shift):
        return self.filter(shifts=shift)


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def trained_for(self, shift):
        return self.get_queryset().trained_for(shift)


class EmployeeTrainingMixin(models.Model):
    class Meta:
        abstract = True

    def available_shifts(self):
        from frate.sft.models import Shift

        return Shift.objects.filter(
            pk__in=self.shifttraining_set.filter(is_active=True).values_list(
                "shift__pk", flat=True
            )
        )

    def unavailable_shifts(self):
        from frate.sft.models import Shift

        return Shift.objects.filter(
            pk__in=self.shifttraining_set.filter(is_active=False).values_list(
                "shift__pk", flat=True
            )
        )

    def untrained_shifts(self):
        return self.department.shifts.exclude(
            pk__in=self.shifttraining_set.values_list("shift__pk", flat=True)
        )


class Employee (BaseEmployee, EmployeeTemplateSetBuilderMixin, EmployeeTrainingMixin):
    
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    initials = models.CharField(max_length=10)
    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, related_name="employees"
    )
    shifts = models.ManyToManyField(
        "Shift", related_name="employees", through="ShiftTraining"
    )
    icon_id = models.CharField(max_length=300, null=True, blank=True)
    start_date = models.DateField(default="2023-02-05")
    is_active = models.BooleanField(default=True)
    fte = models.FloatField(
        default=1.0, validators=[MaxValueValidator(1.0), MinValueValidator(0.0)]
    )
    pto_hours = models.SmallIntegerField(default=10)
    template_week_count = models.PositiveSmallIntegerField(default=2)
    phase_pref = models.ForeignKey(
        "TimePhase",
        to_field="slug",
        on_delete=models.CASCADE,
        related_name="employees",
        null=True,
        blank=True,
    )
    streak_pref = models.PositiveSmallIntegerField(default=3)
    user = models.OneToOneField(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    enrolled_in_inequity_monitoring = models.BooleanField(default=False)
    std_hours_override = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["last_name", "first_name"]

    @property
    def url(self):
        return reverse("dept:empl:detail", args=[self.department.slug, self.slug])

    @property
    def fte_prd(self):
        return int(self.fte * 80)

    @property
    def service_length(self):
        return (timezone.now().date() - self.start_date).days

    objects = EmployeeManager()


class PreferredHoursGuide(models.Model):
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="preferred_hours")
    hours = models.PositiveSmallIntegerField(default=0)
    version = models.ForeignKey("Version", on_delete=models.CASCADE, related_name="preferred_hours",
                                 null=True, blank=True)

    def __str__(self):
        return f"{self.employee}  HoursGuide Sch{self.version.schedule.n} v{self.version.n}"
