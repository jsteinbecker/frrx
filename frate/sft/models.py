from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from frate.basemodels import AutoSlugModel, Weekday


class Shift(AutoSlugModel):

    verbose_name = models.CharField(max_length=300)
    start_time   = models.TimeField()
    hours        = models.SmallIntegerField(default=10)
    phase        = models.ForeignKey('TimePhase', to_field='slug', on_delete=models.CASCADE,
                              related_name='shifts', null=True, blank=True)
    department   = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='shifts')
    is_active    = models.BooleanField(default=True)
    weekdays     = models.ManyToManyField(Weekday, related_name='shifts')
    on_holidays  = models.BooleanField(default=True)
    adjacent_rotating_slot_pref = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['start_time', 'name']

    def __str__(self):
        return self.name

    class Auto:
        @staticmethod
        def set_phase(instance):
            if instance.phase is None:
                instance.phase = instance.department.organization.phases.filter(
                    end_time__gte=instance.start_time).first()

        @staticmethod
        def set_slug(instance):
            if not instance.slug:
                instance.slug = f'{instance.name.lower().replace(" ", "-")}-{instance.department.slug}'

    auto = Auto()

    def save(self, *args, **kwargs):
        created = not self.pk
        self.auto.set_slug(self)
        self.auto.set_phase(self)
        super().save(*args, **kwargs)

    def clean(self):
        if self.weekdays == '':
            raise ValidationError('Weekdays must be specified')
        if self.hours == 0:
            raise ValidationError('Shift hours must be greater than 0')

    def get_absolute_url(self):
        return reverse('dept:sft:detail', args=[self.department.slug, self.slug])

    @property
    def url(self):
        return self.get_absolute_url()
