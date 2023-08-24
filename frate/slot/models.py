from computedfields.models import ComputedFieldsModel, computed
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from frate.empl.models import Employee


class SlotExceedsStreakPrefError(ValidationError):
    pass


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

    def select_options(self):
        from frate.options.models import Option
        return Option.objects.filter(pk__in=self.values('option__pk'))

    def fillable_by(self, empl):
        return self.filter(
            Q(options__employee=empl)
        )


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

    def select_options(self):
        return self.get_queryset().select_options()

    def fillable_by(self, empl):
        return self.get_queryset().fillable_by(empl)


class Slot(ComputedFieldsModel):
    version  = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='slots')
    workday  = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='slots')
    shift    = models.ForeignKey('Shift', on_delete=models.SET_NULL, related_name='slots',
                              null=True, blank=True)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, related_name='slots',
                                 null=True, blank=True, )
    period   = models.ForeignKey('PayPeriod', on_delete=models.SET_NULL, related_name='slots',
                               null=True, blank=True, )
    streak   = models.IntegerField(default=0)

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
        return self.version.schedule.employees.filter(
            Q(shifttraining__shift=self.shift)
        ).exclude(
            Q(pk__in=self.workday.on_pto.values('pk')) |
            Q(pk__in=self.workday.on_tdo.values('pk')) |
            Q(pk__in=self.pre_turnarounds) |
            Q(pk__in=self.post_turnarounds)
        ).distinct()

    def get_next(self):
        if self.workday.next:
            return self.workday.version.slots.filter(shift=self.shift, workday__date__gt=self.workday.date).first()
        return

    def get_prev(self):
        if self.workday.prev:
            return self.workday.version.slots.filter(shift=self.shift, workday__date__lt=self.workday.date).last()
        return

    next = property(get_next)
    prev = property(get_prev)

    def get_preturnarounds(self):
        if self.workday.prev:
            return self.workday.prev.slots.filter(shift__phase__rank__gt=self.shift.phase.rank)
        return Slot.objects.none()

    def get_postturnarounds(self):
        if self.workday.next:
            return self.workday.next.slots.filter(shift__phase__rank__lt=self.shift.phase.rank)
        return Slot.objects.none()

    pre_turnarounds = property(get_preturnarounds)
    post_turnarounds = property(get_postturnarounds)


    def __str__(self):
        return f'{self.workday} {self.shift}'


    def get_absolute_url(self):
        return reverse('dept:sch:ver:wd:slot:detail', kwargs={
            'dept': self.workday.version.schedule.department.slug,
            'sch': self.workday.version.schedule.slug,
            'ver': self.workday.version.n,
            'wd': self.workday.sd_id,
            'sft': self.shift.slug,
        })

    url = property(get_absolute_url)

    class Updater:
        @staticmethod
        def attach_period(self):
            if self.employee and self.period:
                if self.period.employee != self.employee:
                    self.period = self.workday.version.periods.get(employee=self.employee,
                                                                   pd_id=self.workday.pd_id)
            elif self.employee and not self.period:
                self.period = self.workday.version.periods.get(employee=self.employee,
                                                               pd_id=self.workday.pd_id)
            if not self.employee and self.period:
                self.period = None

    def clean(self):
        self.Updater.attach_period(self)

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
        if not created:
            self.clean()
        super().save(*args, **kwargs)
        if not created:
            self.update_options()
        try:
            self._check_pto_requests()
        except ValidationError:
            employee = self.employee
            self.employee = None
            self.save()
            print(f'{employee} is on PTO: {self} automatically cleared employee')


    def update_options(self):
        empls = self.version.schedule.employees \
                    .filter(pk__in=self.shift.employees.all()) \
                    .exclude(pk__in=self.pre_turnarounds.select_employees()) \
                    .exclude(pk__in=self.post_turnarounds.select_employees()) \
                    .exclude(pk__in=self.workday.on_pto.values_list('pk', flat=True))
        for emp in empls:
            self.options.get_or_create(employee=emp)


    def _check_pto_requests(self):
        if self.workday.pto_requests.filter(employee=self.employee).exists():
            raise ValidationError('Employee is on PTO')


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
            pay_period = self.workday.version.periods.filter(employee=employee, pd_id=self.workday.pd_id).first()
            if pay_period and pay_period.discrepancy >= self.shift.hours:
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
            self.set_employee(self.options.viable().first().employee)
            self.save()



    def weekly_hours(self):
        from django.db.models import Sum
        return self.workday.version.slots.filter(employee=self.employee,
                                                 employee__isnull=False,
                                                 workday__wk_id=self.workday.wk_id,
                                                 ).aggregate(Sum('shift__hours'))['shift__hours__sum']


    objects = SlotManager()


