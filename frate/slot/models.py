from computedfields.models import ComputedFieldsModel, computed
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from frate.empl.models import Employee


class SlotQuerySet(models.QuerySet):

    def empty(self):
        return self.filter(employee=None)

    def filled(self):
        return self.exclude(employee=None)

    def direct_templated(self):
        return self.filter(direct_template__isnull=False)

    def rotating_templated(self):
        return self.filter(rotating_templates__isnull=False)

    def generic_templated(self):
        return self.filter(generic_templates__isnull=False)

    def backfill_required(self):
        d_templates = self.filter(direct_template__isnull=False)
        backfill_required = []
        for slot in d_templates:
            if slot.employee:
                continue
            if slot.direct_template.pto_requests.filter(date=slot.workday.date).exists():
                backfill_required.append(slot)
        return self.filter(pk__in=[slot.pk for slot in backfill_required])

    def select_employees(self):
        return Employee.objects.filter(pk__in=self.values('employee__pk'))


class SlotManager(models.Manager):

    def get_queryset(self):
        return SlotQuerySet(self.model, using=self._db)

    def empty(self):
        return self.get_queryset().empty()

    def filled(self):
        return self.get_queryset().filled()

    def backfill_required(self):
        return self.get_queryset().backfill_required()

    def select_employees(self):
        return self.get_queryset().select_employees()


class Slot(ComputedFieldsModel):
    version = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='slots')
    shift = models.ForeignKey('Shift', on_delete=models.SET_NULL, related_name='slots',
                              null=True, blank=True)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, related_name='slots',
                                 null=True, blank=True, )
    period = models.ForeignKey('PayPeriod', on_delete=models.SET_NULL, related_name='slots',
                               null=True, blank=True, )
    streak = models.IntegerField(default=0)

    @computed(models.BooleanField(default=False))
    def exceeds_streak_pref(self):
        if not self.employee:
            return False
        if self.streak > self.employee.streak_pref:
            return True
        return False

    @computed(models.IntegerField(default=0))
    def preference_percentile(self):
        if not self.employee:
            return 0
        if not self.employee.shifttraining_set.filter(shift=self.shift).exists():
            return 0
        if not self.employee.shifttraining_set.filter(shift=self.shift).first().rank:
            return 0
        return self.employee.shifttraining_set.filter(shift=self.shift).first().rank

    direct_template = models.ForeignKey('Employee', on_delete=models.SET_NULL, related_name='direct_template_for',
                                        null=True, blank=True)
    rotating_templates = models.ManyToManyField('Employee', related_name='rotating_template_for', blank=True)
    generic_templates = models.ManyToManyField('Employee', related_name='generic_template_for', blank=True)

    class FilledByChoices(models.TextChoices):
        USER = 'U', 'User'
        MODEL = 'M', 'Model'

    filled_by = models.CharField(max_length=1, choices=FilledByChoices.choices,
                                 default=FilledByChoices.USER, null=True, blank=True)

    @computed(models.BooleanField(default=False))
    def allowed_as_streak_breakpoint(self):
        if not self.get_streak():
            return False
        if len(self.get_streak()) > self.employee.streak_pref:
            if self.employee != self.direct_template and self.employee not in self.rotating_templates.all():
                return True
        else:
            next_slot = self.get_streak().index(self) + 1
            if next_slot >= len(self.get_streak()):
                return False
            if self.employee == self.get_streak()[next_slot].direct_template or \
                    self.employee in self.get_streak()[next_slot].rotating_templates.all():
                return False
            return True
        return False

    class Meta:
        ordering = ['workday__date', 'shift__start_time']
        unique_together = (['workday', 'shift'],
                           ['workday', 'employee'])

    @property
    def employee_options(self):
        from frate.pto.models import PtoRequest

        trained = set(self.shift.employees.filter(pk__in=set(self.workday.version.schedule.employees.values_list('pk', flat=True))).values_list('pk', flat=True))
        if self.workday.get_prev():
            late_yesterday = set(self.workday.get_prev().slots.filter(
                employee__isnull=False,
                shift__phase__rank__gt=self.shift.phase.rank).select_employees().values_list('pk', flat=True))
        else:
            late_yesterday = set()
        if self.workday.get_next():
            early_tomorrow = set(self.workday.get_next().slots.filter(
                employee__isnull=False,
                shift__phase__rank__lt=self.shift.phase.rank).select_employees().values_list('pk', flat=True))
        else:
            early_tomorrow = set()
        on_pto = set(PtoRequest.objects.filter(employee__in=trained, date=self.workday.date).values_list('employee__pk', flat=True))
        on_tdo = set(self.version.schedule.roles.select_slots().filter(leader__type='O', sd_id=self.workday.sd_id).values_list('employees__pk', flat=True))
        already_working = set(self.workday.slots.exclude(pk=self.pk).select_employees().values_list('pk', flat=True))

        available = trained - late_yesterday - early_tomorrow - on_pto - on_tdo - already_working
        print(available)
        return Employee.objects.filter(pk__in=available)


    def get_next(self):
        return self.workday.version.slots.filter(shift=self.shift, workday__date__gt=self.workday.date).first()


    def get_prev(self):
        return self.workday.version.slots.filter(shift=self.shift, workday__date__lt=self.workday.date).last()


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


    @property
    def adjacent_rotating_template_slot(self):
        if not self.shift.adjacent_rotating_slot_pref:
            return None
        if not self.rotating_templates.exists():
            return None
        adjacent = self.shift.adjacent_rotating_slot_pref
        if self.workday.sd_id != 1:
            if self.workday.get_prev().slots.filter(shift=adjacent, rotating_templates__isnull=False).exists():
                return self.workday.get_prev().slots.filter(shift=adjacent, rotating_templates__isnull=False).first()
        if self.workday.get_next():
            if self.workday.get_next().slots.filter(shift=adjacent, rotating_templates__isnull=False).exists():
                return self.workday.get_next().slots.filter(shift=adjacent, rotating_templates__isnull=False).first()
        return None


    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
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


    def _set_hours(self):
        if self.shift:
            if self.hours != self.shift.hours:
                self.hours = self.shift.hours
                self.save()
        else:
            if self.slot_type == 'P' and self.employee:
                self.hours = self.employee.pto_hours
            else:
                self.hours = 0


    def _build_options(self):
        from frate.models import RoleSlot
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


    def _get_role_employees(self):
        from frate.models import RoleSlot
        from frate.empl.models import Employee
        role_slot = RoleSlot.objects.filter(shifts=self.shift, sd_id=self.workday.sd_id)
        if role_slot.exists():
            return role_slot.first().leader.role.employees.all()
        else:
            role_slots = RoleSlot.objects.filter(type='G', sd_id=self.workday.sd_id).values('leader__role__employees')
            return Employee.objects.filter(pk__in=role_slots)


    def set_employee(self, employee=None, filled_by='U'):
        if not employee and self.employee:
            self.employee = None
            self.filled_by = filled_by
            self.save()
            return True, self
        if employee in self.workday.on_deck.all():
            self.employee = employee
            self.filled_by = filled_by
            self.save()
            return True, self
        else:
            print(f'{employee} not in on_deck for {self.workday}')
        return False, self


    def get_streak(self):
        if self.employee:
            d = self.workday
            if d != 1 and self.streak >= 1:
                streak = []
                streak += [self]
                d = d.get_prev()
                if d is not None:
                    while d.slots.filter(employee=self.employee).exists():
                        streak.append(d.slots.filter(employee=self.employee).first())
                        d = d.get_prev()
                        if d is None:
                            break

                d = self.workday
                d = d.get_next()
                if d is not None:
                    while d.slots.filter(employee=self.employee).exists():
                        streak.append(d.slots.filter(employee=self.employee).first())
                        d = d.get_next()
                        if d is None:
                            break

                streak = sorted(streak, key=lambda x: x.workday.date)
                return streak


    def solve(self):
        if self.options.exists():
            self.set_employee(self.options.first().employee)
            self.save()


    def weekly_hours(self):
        from django.db.models import Sum
        return self.workday.version.slots.filter(employee=self.employee,
                                                 employee__isnull=False,
                                                 workday__wk_id=self.workday.wk_id,
                                                 ).aggregate(Sum('shift__hours'))['shift__hours__sum']


    objects = SlotManager()


