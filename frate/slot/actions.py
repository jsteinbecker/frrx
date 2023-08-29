from django.db.models import OuterRef, Subquery, F, Value, Sum
from django.shortcuts import get_object_or_404, redirect

from .models import Slot
from frate.models import PayPeriod, Employee, Workday, Version, ShiftTraining


class SlotActions:

    model = Slot

    @staticmethod
    def solve_direct_template_slot(slot):
        if slot.direct_template:
            if slot.direct_template not in slot.workday.on_pto.all() and \
                slot.direct_template not in slot.workday.on_tdo.all() and \
                slot.direct_template not in slot.workday.slots.exclude(pk=slot.pk).select_employees():
                slot.employee = slot.direct_template
                slot.save()
                print(f'<{slot}>.solve_direct_template_slot() solved by direct template. Assignment={slot.employee}')
                return True


    @staticmethod
    def solve(slot):
        slot.save()

        if slot.employee:
            print(f'<{slot}>.solve() not performed: slot already has employee.')
            return

        if slot.direct_template:
            print(f'<{slot}>.solve() deferred to SlotActions.solve_direct_template_slot()')
            SlotActions.solve_direct_template_slot(slot)
            return

        day = slot.workday
        empls_on_day = day.slots.select_employees()

        print(slot.options.count(), 'options')

        # Get the potential employees by ordering their pay periods by discrepancy
        # employees = list(day.version.periods.filter(pd_id=day.pd_id, employee__shifts=slot.shift) \
        #                     .order_by('-discrepancy',) \
        #                     .values_list('employee__slug', flat=True))
        options = slot.options.exclude(employee__pk__in=empls_on_day.values('pk')).order_by('abs_discrepancy', '-score')

        if options.exists():
            # Get the employee with the least discrepancy
            employee = options[0].employee
            slot.employee = employee
            slot.save()
            return True

        return False



    @staticmethod
    def solve2(slot):
        day = slot.workday
        on_pto = day.on_pto
        on_tdo = day.on_tdo
        trained_employees = day.version.schedule.employees.filter(shifts=slot.shift)\
            .annotate(
                shift_pref=Subquery(ShiftTraining.objects.filter(
                                employee=OuterRef('pk'),
                                shift=slot.shift)\
                            .values('rank_percent')))\
            .annotate(
                on_pto=Value(on_pto.filter(pk=F('pk')).exists()))\
            .annotate(
                on_tdo=Value(on_tdo.filter(pk=F('pk')).exists()))\
            .annotate(
                discrepancy=Sum(slot.version.periods.filter(pd_id=slot.workday.pd_id).values('discrepancy')))\
            .order_by('on_pto', 'on_tdo', '-discrepancy', 'shift_pref')


        if trained_employees:
            slot.set_employee(trained_employees[0])
            return True

    @staticmethod
    def solve3(slot):
        from frate.api.views import SlotOptionSet, CustomOption
        opts = SlotOptionSet(slot)
        if opts.best_option:
            slot.set_employee(opts.best_option.employee)
            return True



