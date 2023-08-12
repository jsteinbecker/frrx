from django.db import models


class VersionQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=self.model.StatusChoices.PUBLISHED)

    def draft(self):
        return self.filter(status=self.model.StatusChoices.DRAFT)

    def archived(self):
        return self.filter(status=self.model.StatusChoices.ARCHIVED)

    def best(self):
        return self.filter(is_best=True)


class VersionManager(models.Manager):
    def get_queryset(self):
        return VersionQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def draft(self):
        return self.get_queryset().draft()

    def archived(self):
        return self.get_queryset().archived()

    def best(self):
        return self.get_queryset().best()



