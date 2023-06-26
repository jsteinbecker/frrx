from django.core.validators import BaseValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum


class DirectRoleSlotValidator(BaseValidator):

    message = 'Direct template slots must be unique for each employee and shift.'
    code = 'direct_rts_unique'

    def clean(self, instance):
        if instance.type == 'D' and instance.template_slots.filter(
                type='D',
                shift=instance.shift,
                employee=instance.employee) \
            .exclude(pk=instance.pk) \
            .exists():

                raise ValidationError(
                    self.message,
                    code=self.code,
                    params={'value': instance},
                )


class RoleEmployeeValidator(BaseValidator):

    message = 'Role Employees must not exceed Role capacity.'
    code = 'role_capacity'

    def clean(self, instance):
        if instance.employees.count() > instance.max_employees:
            raise ValidationError(
                self.message,
                code=self.code,
                params={'value': instance},
            )

class SlotOvertimeValidator(BaseValidator):

    message = 'Slot overtime must not exceed 24 hours.'
    code = 'slot_overtime'

    def clean(self, instance):
        wk = instance.workday.wk_id
        wk_hours = instance.workday.version.slots.filter(employee=instance.employee,
                                                         workday__wk_id=wk) \
                                                         .aggregate(hours=Sum('hours'))['hours'] or 0
        if wk_hours > 40:
            raise ValidationError(
                self.message,
                code=self.code,
                params={'value': instance},
            )
