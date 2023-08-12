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