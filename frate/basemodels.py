import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify



class AutoSlugModel(models.Model):
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70, unique=True)

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