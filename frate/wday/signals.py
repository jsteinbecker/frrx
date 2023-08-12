from django.dispatch import receiver
from django.db.models.signals import post_save

from frate.models import RoleSlot
from frate.role.models import Role
from frate.wday.models import Workday


class Constructors:

    @staticmethod
    @receiver(post_save, sender=Workday)
    def create_slots(sender, instance, created, **kwargs):
        from frate.slot.models import Slot

        if not created: return

        for shift in instance.weekday.shifts.filter(department=instance.version.schedule.department):
            slot = instance.slots.create(
                                    shift=shift,
                                    version=instance.version,)  # type: Slot
            slot.save()




class Editors:

    @staticmethod
    @receiver(post_save, sender=Workday)
    def remove_pto_options(sender, instance, **kwargs):
        pass