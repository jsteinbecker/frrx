from frate.models import *
from django.db.models import F

from typing import Tuple
from dataclasses import dataclass

from frate.ver.models import Version


@dataclass
class UnfavSlotTradeProtocol:

    version: Version

    def get_most_unfavorable_employee(self) :
        """
        Get the most unfavorable employee
        """

        employees  = self.version.schedule.employees.filter(enrolled_in_inequity_monitoring=True)

        data = { employee.slug.upper(): self.version.slots.filter(employee=employee)\
                                                    .exclude(shift__phase=employee.phase_pref).count() \
                                                    for employee in employees }

        max_empl = max(data, key=data.get)

        return max_empl

    def get_most_favorable_employee(self) :
        """
        Get the most favorable employee

        :param request: request
        :param dept: department slug
        :param sch: schedule slug
        :param ver: version number

        :return: JsonResponse"""

        employees  = self.version.schedule.employees.filter(enrolled_in_inequity_monitoring=True)

        data = { employee.slug.upper(): self.version.slots.filter(employee=employee)\
                                                    .filter(shift__phase=employee.phase_pref).count() \
                                                    for employee in employees }

        max_empl = max(data, key=data.get)

        return max_empl

    def get_edge_employees(self) -> Tuple[Employee, Employee]:
        return (self.get_most_unfavorable_employee(), self.get_most_favorable_employee())

    def tradeable_slots(self):

        empl1 = self.get_most_unfavorable_employee()
        empl2 = self.get_most_favorable_employee()

        unfavs = self.version.slots.filter(employee__slug__icontains=empl1).exclude(shift__phase=F('employee__phase_pref'))
        favs = self.version.slots.filter(employee__slug__icontains=empl2, shift__phase=F('employee__phase_pref'))

        data = {}

        for slot in unfavs:
            slot._build_options()
            print(slot.options.all())
            slot.save()

            if slot.options.filter(employee=empl2).exists():
                if not data[slot.slug][f"{empl2.slug.upper()} CAN FILL"]:
                    data[slot.slug][f"{empl2.slug.upper()} CAN FILL"] = [ slot.options.get(employee=empl2).slug ]
                else:
                    data[slot.slug][f"{empl2.slug.upper()} CAN FILL"].append(slot.options.get(employee=empl2).slug)

        return data









