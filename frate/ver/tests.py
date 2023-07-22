from django.test import TestCase
from frate.models import *
from .calculate import calc_n_ptoreqs
from .models import Version
from ..empl.models import Employee


class TestVersionCalculators(TestCase):

    fixtures = ['frate/test-data.yaml']

    def setUp(self):
        dept = Department.objects.first()
        sch = dept.schedules.create()
        sch.save()
        print(sch)

        empl = Employee.objects.first()
        ptoreq = empl.pto_requests.create(date=datetime.date(2023, 2, 11))
        ptoreq.save()
        ptoreq = empl.pto_requests.create(date=datetime.date(2023, 2, 12))
        ptoreq.save()

    def test_calc_n_ptoreqs(self):
        """Test the calc_n_ptoreqs function."""
        version = Version.objects.last()
        n_ptoreqs = calc_n_ptoreqs(version)
        self.assertEqual(n_ptoreqs, 2)
