from django.db.models import Avg
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from .models import Shift


@receiver(post_save, sender=Shift)
def shift_assign_phase_if_not_set(sender, instance, **kwargs):
    if instance.pk and instance.phase is None:
        instance.phase = instance.department.organization.phases.filter(
            end_time__gte=instance.start_time).first()
        instance.save()


@receiver(pre_save, sender=Shift)
def shift_is_niche(sender, instance, **kwargs):
    if instance.pk:
        if instance.employees.count() <= instance.department.employees.filter(is_active=True).count() * 0.25:
            instance.is_niche = True


@receiver(pre_save, sender=Shift)
def shift_relative_ranks(sender, instance, **kwargs):
    if instance.pk:
        if instance.is_niche:
            instance.preference_score = None
            instance.relative_rank = None
            return
        else:
            instance.preference_score = instance.shifttraining_set.filter(shift__is_niche=False).aggregate(
                                                Avg('rank_percent')
                                                )['rank_percent__avg']
            instance.relative_rank = instance.department.shifts.filter(
                                    preference_score__lt=instance.preference_score).count() + 1


