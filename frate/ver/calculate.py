from frate.pto.models import PtoRequest
from frate.ver.models import Version


def calc_n_ptoreqs(version:Version) -> int:
    """Calculate the number of PTO requests for a given version."""
    n = PtoRequest.objects.filter(
        date__gte=version.schedule.start_date,
        date__lte=version.workdays.last().date,
        employee__in=version.schedule.employees.all()
        ).count()
    return n


def calc_empl_quantity_of_streaks(version:Version, employee) -> int:
    n_streaks = 0

    for slot in version.slots.filter(employee=employee):
        if slot == slot.get_streak()[0]:
            n_streaks += 1

    return n_streaks




