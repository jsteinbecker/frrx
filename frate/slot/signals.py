from frate.models import *
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save, post_delete
from frate.models import PayPeriod




@receiver(pre_save, sender=Slot)
def set_streak(sender, instance, **kwargs):
    if instance.pk:
        if instance.employee is not None:
            if instance.workday.sd_id > 0:
                d = instance.workday.get_prev()
                i = 1
                while d and d.slots.filter(employee=instance.employee).exists():
                    d = d.get_prev()
                    i += 1
                instance.streak = i
            else:
                instance.streak = 1
        else:
            instance.streak = 0


@receiver(post_save, sender=Slot)
def build_options(sender, instance, created, **kwargs):
    from frate.options.models import Option

    if not created: return

    empls = instance.workday.version.schedule.employees.all()
    trained = empls.trained_for(instance.shift)

    for employee in trained:
        if employee in instance.workday.on_deck.filter(shifts=instance.shift):
            opt = Option.objects.create(slot=instance, employee=employee)
            opt.save()



@receiver(post_save, sender=Slot)
def set_streak(sender, instance, **kwargs):
    if instance.pk:
        if instance.employee is not None:
            streak = instance.get_streak()
            if streak:
                length = len(streak)
                return
            length = 1
            return
        length = 0
        if instance.streak != length:
            instance.streak = length
            instance.save()


@receiver(post_save, sender=Slot)
def set_templates_templates(sender, instance, created, **kwargs):
    if not created: return
    from frate.models import RoleSlot

    for leader_type in ['D', 'R', 'G']:
        owner_role_slot = RoleSlot.objects.filter(sd_id=instance.workday.sd_id,
                                                  shifts=instance.shift,
                                                  leader__type=leader_type,
                                              ).select_related('leader__role') \
                                      .prefetch_related('leader__role__employees')
        if owner_role_slot.exists():
            role = owner_role_slot.first().leader.role
            print(role.employees.all())
            if leader_type == 'D':
                instance.direct_template = role.employees.first()
            elif leader_type == 'R':
                instance.rotating_templates.set(role.employees.all())
            elif leader_type == 'G':
                instance.generic_tempaltes.set(role.employees.all())
            instance.save()
        return


@receiver(post_save, sender=Slot)
def signal_period_update(sender, instance, **kwargs):
    if instance.employee is None: return
    if instance.period:
        if instance.employee != instance.period.employee:
            instance.period = PayPeriod.objects.get(employee=instance.employee,
                                                pd_id=instance.workday.version.schedule.pd_id,
                                                version=instance.workday.version)
        instance.period.save()


@receiver(post_save, sender=Slot)
def update_options(sender, instance, **kwargs):
    for option in instance.options.all():
        option.save()
