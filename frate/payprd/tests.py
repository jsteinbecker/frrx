from django.test import TestCase

class PayPeriodTests(TestCase):

    fixtures = ['frate/test-data.yaml', ]
    
    def setUp(self):
        from frate.models import Department
        
        dept = Department.objects.get(slug='cpht')
        self.dept = dept

        self.assertTrue(Department.objects.filter(slug='cpht').exists())

    def test_payperiod_creation(self):
    
        from frate.models import Department

        dept = Department.objects.get(slug='cpht')
        sch = dept.schedules.create()
        sch.save()
        ppds = list(set(sch.versions.first().workdays.values_list('pd_id', flat=True)))

        print("DEPARTMENT:", dept)
        print("SCHEDULE:", sch)
        print("PAY PERIOD NUMBERS:", ppds)

        self.assertEqual(len(ppds), 3)
        self.assertEqual(ppds, [1, 2, 3])

        ver = sch.versions.first()
        print("PAY PERIOD COUNT:", ver.periods.count())


