from django.db import models
from django.db.models import F


class SlotQuerySet(models.QuerySet):

    def filled(self):
        return self.exclude(employee=None)

    def unfilled(self):
        return self.filter(employee=None)

    def empty(self):
        return self.filter(employee=None)


class ShiftSlotManager(models.Manager):

    def get_queryset(self):
        return SlotQuerySet(self.model, using=self._db)

    def get_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().get_or_create(*args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().update_or_create(*args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_create(*args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update(*args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update_or_create(*args, **kwargs)

    def update(self, *args, **kwargs):
        from frate.models import Slot
        return super().update(*args, **kwargs)

    def filter(self, *args, **kwargs):
        from frate.models import Slot
        return super().filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        from frate.models import Slot
        return super().exclude(*args, **kwargs)

    def filled(self):
        return self.exclude(employee=None)

    def empty(self):
        return self.filter(employee=None)

    def unfavorables(self):
        return self.exclude(shift__phase=F('employee__phase_pref')).exclude(employee__isnull=True)

    def backfill_required(self):
        has_direct = self.filter(direct_template__isnull=False)
        backfill_required = []
        for slot in has_direct:
            if slot.direct_template.pto_requests.filter(date=slot.workday.date).exists():
                backfill_required.append(slot)
        return self.filter(pk__in=[slot.pk for slot in backfill_required])


class PtoSlotManager(models.Manager):

    def get_queryset(self):
        from frate.models import Slot
        return super().get_queryset().filter(slot_type=Slot.SlotTypeChoices.PTO)

    def create(self, *args, **kwargs):
        from frate.models import Slot
        return super().create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().get_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().update_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update_or_create(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def update(self, *args, **kwargs):
        from frate.models import Slot
        return super().update(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def filter(self, *args, **kwargs):
        from frate.models import Slot
        return super().filter(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        from frate.models import Slot
        return super().exclude(slot_type=Slot.SlotTypeChoices.PTO, *args, **kwargs)


class TdoSlotManager(models.Manager):

    def get_queryset(self):
        from frate.models import Slot
        return super().get_queryset().filter(slot_type=Slot.SlotTypeChoices.TDO)

    def create(self, *args, **kwargs):
        from frate.models import Slot
        return super().create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().get_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().update_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def bulk_update_or_create(self, *args, **kwargs):
        from frate.models import Slot
        return super().bulk_update_or_create(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def update(self, *args, **kwargs):
        from frate.models import Slot
        return super().update(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def filter(self, *args, **kwargs):
        from frate.models import Slot
        return super().filter(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        from frate.models import Slot
        return super().exclude(slot_type=Slot.SlotTypeChoices.TDO, *args, **kwargs)