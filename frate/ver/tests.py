from django.test import TestCase
from frate.models import *
from .calculate import calc_n_ptoreqs
from .models import Version
from ..empl.models import Employee
from frate.slot.protocols import RotatingTemplateAssignmentProtocol


class TestVersionCalculators(TestCase):

    fixtures = [
            "frate/weekdays-data.yaml",
            "frate/org-data.yaml",
            "frate/dept-data.yaml",
            "frate/phase-data.yaml",
            "frate/shift-data.yaml",
            "frate/employee-data.yaml",
        ]

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

    def test_rotating_slot_protocol(self):
        version = Version.objects.last()
        results = []
        for slot in version.slots.filter(rotating_templates__isnull=False):
            protocol = RotatingTemplateAssignmentProtocol(slot)
            result = protocol.execute()
            results.append(result)
        print(results)

    def test_deletions(self):
        schedule = Schedule.objects.last()
        schedule.versions.create(n=2)
        version = Version.objects.last()
        self.assertEqual(Version.objects.count(), 2)
        version.delete()

        print(Version.objects.count())
        self.assertEqual(Version.objects.count(), 1)

    def test_calculating_total_streaks_in_version(self):
        from .calculate import calc_empl_quantity_of_streaks

        version = Version.objects.last()

        print("Total Slots = ", version.slots.count())
        print(f"Pct. Assigned = {version.percent}%")

        op_slots = version.slots.filter(shift__name="OP")
        print(len(op_slots))
        brittanie = Employee.objects.get(name__contains="Brittanie")
        print(brittanie, brittanie.shifts.all())
        
        for slot in op_slots:
            slot.set_employee(brittanie)

        print("Solving...")
        version.save()
        print(f"Pct. Assigned = {version.percent}%")

        n_streaks = calc_empl_quantity_of_streaks(version, brittanie)
        print(n_streaks)

        self.assertEqual(n_streaks, 6)

        josh = Employee.objects.get(name__contains="Josh")

        random_slots = [
                version.slots.get(workday__sd_id=2, shift__name="S"),
                version.slots.get(workday__sd_id=3, shift__name="S"),
                version.slots.get(workday__sd_id=4, shift__name="S"),
                version.slots.get(workday__sd_id=12, shift__name="EI"),
                version.slots.get(workday__sd_id=14, shift__name="EI"),
                version.slots.get(workday__sd_id=15, shift__name="EI"),
            ]

        for slot in random_slots:
            slot.set_employee(josh)

        n_streaks = calc_empl_quantity_of_streaks(version, josh)

        print(n_streaks)
        self.assertEqual(n_streaks, 3)
