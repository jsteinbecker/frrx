from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from frate.empl.models import Employee
from frate.managers import ShiftSlotManager,PtoSlotManager,TdoSlotManager

from frate.validators import SlotOvertimeValidator
from computedfields.models import ComputedFieldsModel, computed


class Slot(ComputedFieldsModel):
    version  = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='slots')
    workday  = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='slots')
    shift    = models.ForeignKey('Shift', on_delete=models.SET_NULL, related_name='slots', null=True, blank=True)
    hours    = models.IntegerField(default=0)
    employee = models.ForeignKey('EmployeeDayToken', on_delete=models.SET_NULL, related_name='slots', null=True, blank=True,
                                 validators=[SlotOvertimeValidator],
                                 limit_choices_to={'is_active':True})

    @computed(models.ForeignKey('PayPeriod', on_delete=models.SET_NULL, related_name='slots', null=True, blank=True),
        depends=[('self',['employee'])])
    def period(self):
        if self.employee:
            return self.version.periods.get(pd_id=self.workday.pd_id, employee=self.employee)
        else:
            return None

    @computed(models.IntegerField(default=0))
    def streak(self):
        if self.employee:
            streak = self.get_streak()
            if streak:
                return len(streak)
            return 1
        else:
            return 0

    @computed(models.BooleanField(default=False))
    def exceeds_streak_pref(self):
        if not self.employee:
            return False
        if self.streak > self.employee.streak_pref:
            return True
        return False


    @computed(models.ForeignKey('Employee', on_delete=models.SET_NULL,related_name='direct_template_for',
                                        null=True, blank=True))
    def direct_template(self):
        from frate.models import RoleSlot
        dept = self.version.schedule.department
        if RoleSlot.objects.filter(leader__role__department=dept,
                                   shifts=self.shift,
                                   type='D',
                                   sd_id=self.workday.sd_id).exists():
            return RoleSlot.objects.get(leader__role__department=dept,
                                           shifts=self.shift,
                                           type='D',
                                           sd_id=self.workday.sd_id).employees.first()
        return
    rotating_templates = models.ManyToManyField('Employee',related_name='rotating_template_for', blank=True)
    generic_templates  = models.ManyToManyField('Employee',related_name='generic_template_for', blank=True)

    class FilledByChoices(models.TextChoices):
                    USER= 'U', 'User'
                    MODEL= 'M', 'Model'

    filled_by  = models.CharField(max_length=1, choices=FilledByChoices.choices,
                                  default=FilledByChoices.USER,
                                  null=True, blank=True)

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

    def clean_filled_by(self):
        print('clean_filled_by')
        if self.employee:
            self.filled_by = None

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


    def clean(self):
        self._check_slot_type_valid()
        self.clean_filled_by()
        super().clean()

    def _get_role_employees(self):
        from frate.models import RoleSlot
        from frate.empl.models import Employee
        role_slot = RoleSlot.objects.filter(shifts=self.shift, sd_id=self.workday.sd_id)
        if role_slot.exists():
            return role_slot.first().leader.role.employees.all()
        else:
            role_slots = RoleSlot.objects.filter(type='G', sd_id=self.workday.sd_id).values('leader__role__employees')
            return Employee.objects.filter(pk__in=role_slots)

    def set_employee(self, employee, filled_by='U'):
        if not employee and self.employee:
            self.employee = None
            self.filled_by = filled_by
            self.save()
            return True, self
        if employee in self.options.values('employee'):
            self.employee = employee
            self.filled_by = filled_by
            self.save()
            return True, self
        return False, self

    def get_streak(self):
        if self.employee:
            d = self.workday
            if d != 1 and self.streak > 1:
                streak = []
                streak += [self]
                d = d.get_prev()
                if d != None:
                    while d.slots.filter(employee__employee=self.employee).exists():
                        streak.append(d.slots.filter(employee=self.employee).first())
                        d = d.get_prev()
                        if d == None:
                            break

                d = self.workday
                d = d.get_next()
                if d != None:
                    while d.slots.filter(employee=self.employee).exists():
                        streak.append(d.slots.filter(employee=self.employee).first())
                        d = d.get_next()
                        if d == None:
                            break

                streak = sorted(streak, key=lambda x: x.workday.date)
                return streak

    def conflict_blockers(self) -> 'QuerySet[Employee]':
        from frate.empl.models import Employee
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
        from frate.empl.models import Employee
        out = []
        for empl in self.version.schedule.employees.all():
            prd_hours = sum(list(self.workday.version.slots.filter(employee=empl,
                                                                   workday__pd_id=self.workday.pd_id).values_list(
                'shift__hours', flat=True)))
            if prd_hours + self.hours > empl.fte * 80:
                out.append(empl.pk)
        return Employee.objects.filter(pk__in=out)

    def solve(self):
        from frate.empl.models import Employee
        if not self.shift:
            return
        trained = self.options.filter(employee__shifts=self.shift)
        blocked = self.options.filter(pk__in=self.conflict_blockers().values_list('pk', flat=True))

        available = trained.exclude(pk__in=self.conflict_blockers().values_list('pk', flat=True)).order_by('?')
        at_fte = self.fte_blockers()

        templated_off = self.workday.on_tdo

        available = available.exclude(pk__in=at_fte.values_list('pk', flat=True))\
                             .exclude(pk__in=templated_off)\
                             .exclude(pk__in=blocked.values_list('pk', flat=True))\
                             .order_by('?')

        if available.exists():
            self.set_employee(available.first(), filled_by=self.FilledByChoices.MODEL)

    def weekly_hours(self):
        from django.db.models import Sum
        return self.workday.version.slots.filter(employee=self.employee,
                                                 employee__isnull=False,
                                                 workday__wk_id=self.workday.wk_id,
                                                 ).aggregate(Sum('shift__hours'))['shift__hours__sum']

    objects = ShiftSlotManager()
    pto_slots = PtoSlotManager()
    tdo_slots = TdoSlotManager()


class TokenQuerySet(models.QuerySet):

    def on_deck(self):
        return self.filter(position='DECK')

    def on_tdo(self):
        return self.filter(position='TDO')

    def on_pto(self):
        return self.filter(position='PTO')

    def working(self):
        return self.exclude(position__in=['PTO', 'TDO', 'DECK'])


class TokenManager(models.Manager):

    def get_queryset(self):
        return TokenQuerySet(self.model, using=self._db)

    def on_deck(self):
        return self.get_queryset().on_deck()

    def on_tdo(self):
        return self.get_queryset().on_tdo()

    def on_pto(self):
        return self.get_queryset().on_pto()

    def working(self):
        return self.get_queryset().working()


class EmployeeDayToken(ComputedFieldsModel):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='tokens', editable=False)
    workday = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='tokens', editable=False)
    position = models.CharField(max_length=10, default='DECK')

    class Meta:
        unique_together = ('employee', 'workday')

    def __str__(self): return f'{self.employee} {self.workday} TOKEN'

    objects = TokenManager()