from django.db import models


class OptionQuerySet(models.QuerySet):

    def viable(self):
        return self.filter(is_viable=True)

    def unviable(self):
        return self.filter(is_viable=False)

    def entitled(self):
        return self.filter(entitled=True)

    def as_pick_up(self):
        return self.filter(fill_method=Option.FillMethod.PICK_UP)


class OptionManager(models.Manager):

    def get_queryset(self):
        return OptionQuerySet(self.model, using=self._db)

    def viable(self):
        return self.get_queryset().viable()

    def unviable(self):
        return self.get_queryset().unviable()

    def entitled(self):
        return self.get_queryset().entitled()

    def as_pick_up(self):
        return self.get_queryset().as_pick_up()


class Option(models.Model):
    """OPTION (model)

    ==============

    A Fill Option for a Slot

    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='options')
    slot     = models.ForeignKey('Slot', on_delete=models.CASCADE, related_name='options')
    pay_period = models.ForeignKey('PayPeriod', on_delete=models.CASCADE, related_name='options',
                                   null=True, blank=True)
    affinity_score = models.IntegerField(default=0)

    class FillMethod(models.TextChoices):
        PICK_UP = 'P', 'Pick Up'
        TRADE = 'T', 'Trade'
        INTO_OVERTIME = 'O', 'Pick Up Into Overtime'
        BREAK_PTO = 'B', 'Break PTO'
        BREAK_TDO = 'D', 'Break TDO'
    fill_method = models.CharField(max_length=1, choices=FillMethod.choices, default=FillMethod.PICK_UP)
    preference = models.IntegerField(default=0)
    must_trade = models.BooleanField(default=False)
    week_hours = models.IntegerField(default=0)
    period_hours = models.IntegerField(default=0)
    entitled = models.BooleanField(default=False)
    discrepancy = models.IntegerField(default=0)
    marked_as_off = models.BooleanField(default=False)
    is_viable = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.employee} {self.slot}'

    class Meta:
        verbose_name = 'Option'
        verbose_name_plural = 'Options'
        ordering = ['slot', '-entitled', '-affinity_score']
        unique_together = ['employee', 'slot']

    class Updater:
        @staticmethod
        def clean_fill_method(self):
            if self.employee in self.slot.workday.slots.exclude(pk=self.slot.pk).values_list('employee', flat=True):
                return self.FillMethod.TRADE
            elif self.period_hours + self.slot.shift.hours > 80:
                return self.FillMethod.INTO_OVERTIME
            elif self.employee.pto_requests.filter(date=self.slot.workday.date).exists():
                return self.FillMethod.BREAK_PTO
            elif self.slot.workday.on_tdo.filter(pk=self.employee.pk).exists():
                return self.FillMethod.BREAK_TDO
            else:
                return self.FillMethod.PICK_UP

        @staticmethod
        def clean_preference(self):
            pref = self.employee.shifttraining_set.filter(shift=self.slot.shift)
            if pref.exists():
                return 100 - pref.first().rank_percent
            else:
                return 50

        @staticmethod
        def clean_pay_period(self):
            """Links the proper pay period based on assigned employee"""
            prd = self.slot.version.periods.filter(
                pd_id=self.slot.workday.pd_id,
                employee=self.employee)
            if prd.exists():
                return prd.first()
            else:
                return None

        @staticmethod
        def clean_week_hours(self):
            return self.slot.version.slots.filter(
                employee=self.employee,
                workday__wk_id=self.slot.workday.wk_id) \
                .aggregate(models.Sum('shift__hours'))['shift__hours__sum'] or 0

        @staticmethod
        def clean_period_hours(self):
            return self.slot.version.slots.filter(
                employee=self.employee,
                workday__pd_id=self.slot.workday.pd_id) \
                .aggregate(models.Sum('shift__hours'))['shift__hours__sum'] or 0

        @staticmethod
        def clean_entitled(self):
            return self.slot.direct_template == self.employee

        @staticmethod
        def clean_discrepancy(self):
            if self.slot.version.schedule.employee_hours_overrides.filter(employee=self.employee).exists():
                goal = self.slot.version.schedule.employee_hours_overrides.get(employee=self.employee).hours
            else:
                goal = self.employee.fte * 80
            if self.pay_period:
                self.pay_period.save()
                hours = self.pay_period.hours
            else:
                hours = 0
            return hours - goal

        @staticmethod
        def clean_must_trade(self):
            empl = self.employee
            day = self.slot.workday
            if day.slots.filter(employee=empl).exclude(workday__pk=day.pk).exists():
                return True
            else:
                return False

        @staticmethod
        def clean_marked_as_off(self):
            if self.slot.workday.on_tdo.filter(pk=self.employee.pk).exists():
                return True
            elif self.slot.workday.on_pto.filter(pk=self.employee.pk).exists():
                return True
            else:
                return False

        @staticmethod
        def clean_is_viable(self):
            if self.fill_method in [self.FillMethod.PICK_UP, self.FillMethod.TRADE]:
                if self.discrepancy < 0 and self.week_hours <= 40:
                    if not self.marked_as_off:
                        return True
            return False

        @staticmethod
        def clean_affinity_score(self):

            # step 1: Base Score on Pick-up/Trade/Overtime/PTO-break
            # step 2: Adjust for Employees Preference for Shift
            # step 3: Adjust for Employees Difference in Missing Hours for Period

            # step 1
            if self.fill_method == self.FillMethod.PICK_UP:
                base = 100
            elif self.fill_method == self.FillMethod.TRADE:
                base = 80
            elif self.fill_method == self.FillMethod.INTO_OVERTIME:
                base = 20
            else: base = 0

            # step 2
            training = self.employee.shifttraining_set.filter(shift=self.slot.shift)
            if training.exists():
                score = base - training.first().rank_percent
            else: score = base

            # step 3
            avg_discrepancy = self.slot.version.schedule.employee_hours_overrides \
                                .aggregate(models.Avg('hours'))['hours__avg']
            if avg_discrepancy:
                if avg_discrepancy < self.discrepancy < 0:
                    # discrepancy > avg == more hours than avg
                    score = score - 15
                elif self.discrepancy > 0:
                    score -= 70

            if score < 0: score = 0

            return score



    updater = Updater()

    def clean(self):
        if not self.pay_period:
            self.pay_period = self.updater.clean_pay_period(self)
        self.fill_method = self.updater.clean_fill_method(self)
        self.week_hours = self.updater.clean_week_hours(self)
        self.period_hours = self.updater.clean_period_hours(self)
        self.entitled = self.updater.clean_entitled(self)
        self.discrepancy = self.updater.clean_discrepancy(self)
        self.must_trade = self.updater.clean_must_trade(self)
        self.preference = self.updater.clean_preference(self)
        self.is_viable = self.updater.clean_is_viable(self)
        self.affinity_score = self.updater.clean_affinity_score(self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    objects = OptionManager()
