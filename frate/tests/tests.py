import random

from django.test import TestCase
from django.urls import reverse

from frate.basemodels import Weekday
from frate.empl.models import Employee
from frate.models import (Organization,
                          Department,
                          RoleSlot)
from frate.role.models import Role
from frate.sch.models import Schedule
from frate.sft.models import Shift


# Create your tests here.


class FlowRateMainTests(TestCase):
    
    fixtures = [
        'frate/weekdays-data.yaml',
        'frate/org-data.yaml',
        'frate/dept-data.yaml',
        'frate/phase-data.yaml',
        'frate/shift-data.yaml',
        'frate/employee-data.yaml',
    ]

    def setUp(self):

        print(Department.objects.all())
        print(Shift.objects.all())
        print(Employee.objects.all())

    def test_organization(self):
        org = Organization.objects.get(name='NCMC')
        cpht = org.departments.get(slug='cpht')

        self.assertEqual(org.name, 'NCMC')
        self.assertEqual(org.verbose_name, 'North Colorado Medical Center')

        self.assertEqual(org.departments.count(), 2)
        self.assertEqual(org.phases.count(), 5)

        self.assertEqual(cpht.shifts.count(), 12)
        self.assertEqual(cpht.shifts.filter(phase__name='AM').count(), 8)
        self.assertEqual(cpht.shifts.filter(phase__name='PM').count(), 2)

        print("ORGANIZATION INFO", org,
              f"SLUG= {org.slug}",
              f"DEPTS= {org.departments.count()}, {','.join([d.name for d in org.departments.all()])}",
              f"PHASES= {org.phases.count()}, {','.join([p.name for p in org.phases.all()])}",
              sep='\n')

    def test_schedule_builds(self):
        from django.test import Client

        dept = Department.objects.get(slug='cpht')

        client = Client()
        response = client.get(reverse('dept:build-new-sch', args=[dept.slug]))

        sch_slug = response.content.decode('utf-8')
        sch = Schedule.objects.get(slug=sch_slug)

        print("SCHEDULE INFO", sch,
              f"SLUG= {sch.slug}",
              f"DEPT= {sch.department}",
              f"ORG=  {sch.department.organization}",
              sep='\n')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(sch.slug, "sch-2023-1")
        self.assertEqual(sch.department, dept)

        print("SCHEDULE INFO", sch,
              f"SLUG= {sch.slug}",
              f"DEPT= {sch.department}",
              f"ORG=  {sch.department.organization}",
              f"EMPLOYEES= {sch.department.employees.count()}, {','.join([e.name for e in sch.department.employees.all()])}",
              f"SHIFTS= {sch.department.shifts.count()}, {','.join([s.name for s in sch.department.shifts.all()])}",
              sep='\n')

    def test_employees(self):
        cpht = Department.objects.get(slug='cpht')

        for empl in cpht.employees.all():
            print(empl.name, ": ", ", ".join(empl.shifts.all().values_list('name', flat=True)))

        from django.db.models import Max, Count
        # get Max Count of shifts on a single employee
        max_shifts = cpht.employees.annotate(
            shift_count=Count('shifts')
        ).aggregate(Max('shift_count'))

        print("MAX SHIFTS", max_shifts)
        self.assertEqual(max_shifts['shift_count__max'], 9)
        # get the Employee who has the most shifts
        max_shifts = cpht.employees.annotate(
            shift_count=Count('shifts')
        ).filter(shift_count=max_shifts['shift_count__max'])

        print("MAX SHIFTS", max_shifts)
        self.assertEqual(max_shifts.count(), 3)
        self.assertEqual(max_shifts[0].name, 'Josh Steinbecker')

    def test_template_slot_creation(self):

        cpht = Department.objects.get(slug='cpht')
        sch = cpht.schedules.create()
        sch.save()

        rand_id = lambda: random.randint(0, cpht.employees.count() - 1)
        rand_id.__doc__ = "Returns a random ID for an employee in the department"

        emp1 = cpht.employees.all()[rand_id()]
        emp2 = cpht.employees.all()[rand_id()]

        ts = emp1.template_schedules.create()
        ts.save()

        # create a template slot
        ts_range = sch.versions.first().workdays.count() // emp1.template_week_count
        print("EMPLOYEE:", emp1.name)
        print("EMPL TEMPLATE SIZE:", f"{emp1.template_week_count} weeks")
        print("TPLSLOT RANGE:", ts_range)

        for i in range(sch.versions.first().workdays.count()):
            tss = ts.template_slots.create(
                employee=emp1,
                sd_id=i,
                type='G',
            )
            if i >= ts_range:
                tss.following = ts.template_slots.filter(sd_id=i % ts_range, employee=emp1).first()
            tss.save()
            print(tss, f"(mirrors: {tss.following.sd_id if tss.following else '-'})")

        for i in range(5):
            j = random.randint(0, ts_range)
            tss = ts.template_slots.filter(
                employee=emp1,
                sd_id=j).first()
            tss.type = 'D'
            tss.direct_shift = Shift.objects.filter(weekdays__abvr=f"SMTWRFA"[i]).order_by('?').first()
            tss.save()

            print(f'TSS: {tss.sd_id} {tss.get_type_display()} ',
                  f'TSS DIRECT TEMPLATE FOR: {tss.direct_shift}')

        print('#GTS:', emp1.template_slots.filter(type='G').count())
        print('#DTS:', emp1.template_slots.filter(type='D').count())

        self.assertEqual(emp1.template_slots.filter(type='G').count() + emp1.template_slots.filter(type='D').count(),
                         emp1.template_slots.all().count())

        for ts in emp1.template_slots.filter(type='D'):
            print(ts.direct_shift, ts.sd_id, "SMTWRFA"[ts.sd_id % 7])

    def test_template_schedule(self):
        emp = Employee.objects.get(name='Josh Steinbecker')
        emp.template_week_count = 3
        emp.save()
        print(f'Employee {emp} Template Week Count: {emp.template_week_count}')
        tsch = emp.template_schedules.create()
        tsch.save()

        sd_ids = [1, 2, 3, 8, 9, 10, 11, 17, 20]
        for tslt in tsch.template_slots.filter(sd_id__in=sd_ids):
            tslt.type = 'O'
            tslt.save()

        self.assertEqual(tsch.template_slots.filter(type='O').count(), len(sd_ids * 2))

        print(f"# of Templates Changed to TEMPLATED OFF (manual): {len(sd_ids)}")
        print(f"# Full Template Schedule TEMPLATED OFF (auto'd):  {tsch.template_slots.filter(type='O').count()}")
        print(tsch.display_template_slot_types().replace(' ', '').replace('"', '').replace('[', '').replace(']', ''))

    def test_weekdays(self):
        """
        TEST WEEKDAYS
        =============
        This test is to ensure that the Weekday model is working as expected.
        """
        print(self.test_weekdays.__doc__)

        cpht = Department.objects.get(slug='cpht')
        print(cpht.name)

        sch = cpht.schedules.create()
        sch.save()
        print(sch, 'days:', sch.versions.first().workdays.count())

        for wd in Weekday.objects.all():
            shifts_display = list(wd.shifts.all().values_list('name', flat=True))

            print(wd.abvr, wd.name, wd.n, shifts_display)
            print()

        for wd in sch.versions.first().workdays.all():
            print(wd.weekday, wd.sd_id)

    def test_role_creation(self):
        d = Department.objects.get(slug='cpht')

        def op_onc():
            rt = d.roles.create(name='OP-ONC',
                                week_count=2,
                                max_employees=1)
            rt.save()

            print(r'\n\n')

            print('ROLE COUNT:', d.roles.count())
            self.assertEqual(d.roles.count(), 1)

            print('ROLE:', d.roles.first().name)
            self.assertEqual(d.roles.first().name, 'OP-ONC')

            print('ROLE WEEK COUNT:', d.roles.first().week_count)
            self.assertEqual(d.roles.first().week_count, 2)

            print('ROLE LEADER-SLOTS COUNT:', d.roles.first().leader_slots.count())
            self.assertEqual(d.roles.first().leader_slots.count(), 14)

            for ls in d.roles.first().leader_slots.all():
                print(ls,
                      "UNASSIGNED SHIFTS:",
                      "/".join(list(ls.unassigned_shifts().values_list('name', flat=True))),
                      "\n")

            for slot in rt.leader_slots.filter(sd_id__in=[2, 3, 4, 5, 6, 9, 10, 11, 12, 13]):
                slot.type = 'D'
                slot.shifts.add(Shift.objects.get(name='OP'))
                slot.save()

            type_string = "".join([slot.type for slot in rt.leader_slots.all()])
            print("TYPE STRING:", type_string)
            self.assertEqual(type_string, "GDDDDDGGDDDDDG")

            # ASSIGN ROLE TO EMPLOYEE
            emp = Employee.objects.get(name='Brittanie Spahn')
            print("EMPLOYEE:", emp)
            rt.employees.add(emp)
            rt.save()

            self.assertEqual(emp.roles.first(), rt)
            print(f"EMPLOYEE {emp} ROLE TEMPLATE SCHEDULE: {emp.roles.first()}")
            print("CORRECTLY ASSIGNED")
            print()
            print()

        def tech_7p_a():
            rt = d.roles.create(name='7P-A',
                                week_count=2,
                                max_employees=1)
            rt.save()

            print();
            print()
            print('ROLE COUNT: ', d.roles.count())
            self.assertEqual(d.roles.count(), 2)

            print('ROLE:',
                  d.roles.last().name)
            self.assertEqual(d.roles.last().name, '7P-A')

            print('ROLE WEEK COUNT:',
                  d.roles.last().week_count)
            self.assertEqual(d.roles.last().week_count, 2)

            print('ROLE LEADER-SLOTS COUNT:', d.roles.last().leader_slots.count())
            self.assertEqual(d.roles.last().leader_slots.count(), 14)

            # for ls in d.role_templates.last().leader_slots.all():
            #     print("SD-ID", ls.sd_id,
            #           "UNASSIGNED", [f"{s.name}" for s in ls.unassigned_shifts()])

            for slot in rt.leader_slots.filter(sd_id__in=[1, 2, 4, 9, 10, 12, 13]):
                slot.type = 'D'
                slot.shifts.add(Shift.objects.get(name='7P'))
                slot.save()

            type_string = "".join([slot.type for slot in rt.leader_slots.all()])
            print("TYPE STRING:", type_string)
            self.assertEqual(type_string, "DDGDGGGGDDGDDG")

            # ASSIGN ROLE TO EMPLOYEE
            emp = Employee.objects.get(name='Brianna Annan')
            print("EMPLOYEE:", emp)
            rt.employees.add(emp)
            rt.save()

            self.assertEqual(emp.roles.first(), rt)
            print(f"EMPLOYEE {emp} ROLE TEMPLATE SCHEDULE: {emp.roles.first()}")
            print("CORRECTLY ASSIGNED")
            print()
            print()

        op_onc()
        tech_7p_a()

        role_slot = RoleSlot.objects.filter(sd_id=4).last()  # type : RoleSlot
        print(role_slot)
        print(role_slot.unassigned_shifts())


class RoleTests(TestCase):

    fixtures = [
            "frate/weekdays-data.yaml",
            "frate/org-data.yaml",
            "frate/dept-data.yaml",
            "frate/phase-data.yaml",
            "frate/shift-data.yaml",
            "frate/employee-data.yaml",
        ]

    def setUp(self):
        dept = Department.objects.get(slug='cpht')

        role_7pA = dept.roles.create(name='TECH-III-7P.A', week_count=2, max_employees=1)
        role_7pA.save()
        role_7pA.leader_slots.filter(sd_id__in=[1, 2, 4, 9, 10, 12, 13]).update(type='D')
        for leader in role_7pA.leader_slots.filter(type='D'):
            leader.shifts.add(Shift.objects.get(name='7P'))
            leader.save()

    def test_role_creation(self):
        role_7pA = Role.objects.get(name='TECH-III-7P.A')
        print(role_7pA.leader_slots.all())

        self.assertEqual(
            list(role_7pA.leader_slots.first().slots.values_list('sd_id', flat=True)),
            [1, 15, 29]
        )


class PtoRequestBackfillTests(TestCase):

    fixtures = [
            "frate/weekdays-data.yaml",
            "frate/org-data.yaml",
            "frate/dept-data.yaml",
            "frate/phase-data.yaml",
            "frate/shift-data.yaml",
            "frate/employee-data.yaml",
        ]

    def setUp(self):
        cpht = Department.objects.get(slug='cpht')
        main_emp = Employee.objects.get(name='Brittanie Spahn')

        sch = cpht.schedules.create()
        sch.save()

        print(sch.versions.first().periods.all())

    def test_pto_creation(self):
        print("","TEST :: PTO CREATION","", sep="\n")
        cpht = Department.objects.get(slug='cpht')
        main_emp = Employee.objects.get(name='Brittanie Spahn')
        ver = cpht.schedules.last().versions.first()
        print(ver)

        pto_dates = list(ver.workdays.filter(sd_id__in=[2, 3, 4, 5]).values_list('date', flat=True))
        print([d.strftime('%a %m/%d') for d in pto_dates])
        for date in pto_dates:
            ptoreq = main_emp.pto_requests.create(date=date)
            ptoreq.save()

        self.assertEqual(main_emp.pto_requests.count(), 4)

    def test_direct_template_pto_requests(self):
        sch = Schedule.objects.last()
        ver = sch.versions.first()
        main_emp = Employee.objects.get(name='Brittanie Spahn')

        op_slots = ver.slots.filter(shift__slug='op-cpht')
        op_slots.update(direct_template=main_emp)
        print("OP Slots:", op_slots.count())

        pto_dates = list(ver.workdays.filter(sd_id__in=[2, 3, 4, 5]).values_list('date', flat=True))
        for date in pto_dates:
            ptoreq = main_emp.pto_requests.create(date=date)
            ptoreq.save()

        backfill_required = ver.slots.backfill_required()

        print("Backfill Required:", backfill_required)
        self.assertEqual(backfill_required.count(), 4)

    def test_period_creation(self):
        dept = Department.objects.get(slug='cpht')
        ver = dept.schedules.last().versions.first()
        ver.save()
        josh = Employee.objects.get(name__contains='Josh S')

        self.assertEqual(
            ver.periods.filter(employee=josh).count(),
            3
        )
