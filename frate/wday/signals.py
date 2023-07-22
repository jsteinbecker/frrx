from django.dispatch import receiver
from django.db.models.signals import post_save

from frate.models import RoleSlot, Role
from frate.wday.models import Workday
from frate.slot.models import EmployeeDayToken





class EmployeeTokenSignals:

    @staticmethod
    @receiver(post_save, sender=Workday)
    def create_tokens(sender, instance, created, **kwargs):

        if created:

            employees = instance.version.schedule.department.employees.filter(is_active=True)

            for emp in employees:

                tok = instance.tokens.create(employee=emp, position='DECK')

                if emp.pto_requests.filter(date=instance.date).exists():
                    tok.position = 'PTO'

                elif RoleSlot.objects.filter(employees=emp,
                                             sd_id=instance.sd_id,
                                             type=Role.TemplateTypeChoices.OFF).exists():
                    tok.position = 'TDO'


                tok.save()










