import datetime
import random

from django.test import TestCase
from django.urls import reverse

from frate.models import (Organization,
                          Department,
                          TimePhase,
                          ShiftTraining,
                          Shift,
                          Employee,
                          EmployeeTemplateSchedule,
                          Schedule,
                          BaseTemplateSlot,
                          Slot)

# Create your tests here.

class FlowRateMainTest(TestCase):
    databases = {'default',}

    def setUp(self) -> None:

        # Organization
        org = Organization.objects.create(name='NCMC',verbose_name='North Colorado Medical Center')
        org.save()

        # Departments
        cpht = org.departments.create(name='CPHT',verbose_name='Technicians',schedule_week_length=6,initial_start_date='2023-02-05')
        cpht.save()
        rph = org.departments.create(name='RPH',verbose_name='Pharmacists',schedule_week_length=6,initial_start_date='2023-02-05')
        rph.save()

        # Time Phases
        am = org.phases.create(name='AM',verbose_name='Morning',end_time='09:30')
        am.save()
        md = org.phases.create(name='MD',verbose_name='Midday',end_time='11:30')
        md.save()
        pm = org.phases.create(name='PM',verbose_name='Afternoon',end_time='14:30')
        pm.save()
        ev = org.phases.create(name='EV',verbose_name='Evening',end_time='18:30')
        ev.save()
        xn = org.phases.create(name='XN',verbose_name='Night',end_time='23:30')
        xn.save()

        # Shifts
        mi = cpht.shifts.create(name='MI',verbose_name='Morning IV',start_time='06:30',hours=10) ; mi.save()
        _7c = cpht.shifts.create(name='7C',verbose_name='Morning Courier',start_time='07:00',hours=10) ; _7c.save()
        _7p = cpht.shifts.create(name='7P',verbose_name='Evening Pharmacy',start_time='07:00',hours=10) ; _7p.save()
        op = cpht.shifts.create(name='OP',verbose_name='Outpatient Oncology',start_time='07:30',hours=8,weekdays='MTWRF') ; op.save()
        s = cpht.shifts.create(name='S',verbose_name='Support',start_time='08:00',hours=10,weekdays='MTWRF') ; s.save()
        ei = cpht.shifts.create(name='EI',verbose_name='Evening IV',start_time='12:30',hours=10) ; ei.save()
        ep = cpht.shifts.create(name='EP',verbose_name='Evening Pharmacy',start_time='12:30',hours=10) ; ep.save()
        _3 = cpht.shifts.create(name='3',verbose_name='Pyxis',start_time='15:00',hours=10) ; _3.save()
        n = cpht.shifts.create(name='N',verbose_name='Night',start_time='20:30',hours=10) ; n.save()

        josh = cpht.employees.create(name='Josh Steinbecker', fte=0.625, pto_hours=10, template_week_count=3); josh.save()
        trisha = cpht.employees.create(name='Trisha Fat', fte=0, pto_hours=10, template_week_count=3); trisha.save()
        sabrina = cpht.employees.create(name='Sabrina Berg', fte=0.5, pto_hours=10, template_week_count=3); sabrina.save()
        tiffany = cpht.employees.create(name='Tiffany Fat', fte=0.5, pto_hours=10, template_week_count=3); tiffany.save()
        brittanie = cpht.employees.create(name='Brittanie Spahn', fte=1, pto_hours=10, template_week_count=2); brittanie.save()

        josh.shifts.add(mi,_7c,_7p,op,s,ei,ep,_3,n); josh.save()
        trisha.shifts.add(mi,_7c,_7p,s,op,ei,ep,_3,n); trisha.save()
        sabrina.shifts.add(mi,_7c,_7p,s,ei,ep,_3,n); sabrina.save()
        tiffany.shifts.add(mi,_7c,s,ei,ep,_3,n); tiffany.save()
        brittanie.shifts.add(op); brittanie.save()

    def test_organization(self):
        org  = Organization.objects.get(name='NCMC')
        cpht = org.departments.get(name='CPHT')

        self.assertEqual(org.name, 'NCMC')
        self.assertEqual(org.verbose_name, 'North Colorado Medical Center')
        self.assertEqual(org.departments.count(), 2)
        self.assertEqual(org.phases.count(), 5)

        self.assertEqual(cpht.shifts.count(), 9)
        self.assertEqual(cpht.shifts.filter(phase__name='AM').count(), 5)
        self.assertEqual(cpht.shifts.filter(phase__name='PM').count(), 2)

        print("ORGANIZATION INFO",org,
              f"SLUG= {org.slug}",
              f"DEPTS= {org.departments.count()}, {','.join([d.name for d in org.departments.all()])}",
              f"PHASES= {org.phases.count()}, {','.join([p.name for p in org.phases.all()])}",
                sep='\n')

    def test_schedule_builds(self):
        from django.test import Client

        dept = Department.objects.get(name='CPHT')

        client   = Client()
        response = client.get( reverse('dept:build-new-sch', args=[dept.slug]))

        sch_slug = response.content.decode('utf-8')
        sch = Schedule.objects.get(slug=sch_slug)

        print("SCHEDULE INFO",sch,
              f"SLUG= {sch.slug}",
              f"DEPT= {sch.department}",
              f"ORG=  {sch.department.organization}",
              sep='\n')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(sch.slug, "sch-2023-1")
        self.assertEqual(sch.department, dept)

        print("SCHEDULE INFO",sch,
              f"SLUG= {sch.slug}",
              f"DEPT= {sch.department}",
              f"ORG=  {sch.department.organization}",
              f"EMPLOYEES= {sch.department.employees.count()}, {','.join([e.name for e in sch.department.employees.all()])}",
              f"SHIFTS= {sch.department.shifts.count()}, {','.join([s.name for s in sch.department.shifts.all()])}",
              sep='\n')

    def test_employees(self):
        cpht = Department.objects.get(name='CPHT')

        for empl in cpht.employees.all():
            print(empl.name,": ", ", ".join(empl.shifts.all().values_list('name', flat=True)))


        from django.db.models import Max, Avg, Min, Count
        # get Max Count of shifts on a single employee
        max_shifts = cpht.employees.annotate(
                        shift_count=Count('shifts')
                        ).aggregate(Max('shift_count'))

        print("MAX SHIFTS",max_shifts)
        self.assertEqual(max_shifts['shift_count__max'], 9)
        # get the Employee who has the most shifts
        max_shifts = cpht.employees.annotate(
                        shift_count=Count('shifts')
                        ).filter(shift_count=max_shifts['shift_count__max'])

        print("MAX SHIFTS",max_shifts)
        self.assertEqual(max_shifts.count(), 2)
        self.assertEqual(max_shifts[0].name, 'Josh Steinbecker')

    def test_template_slot_creation(self):
        cpht = Department.objects.get(name='CPHT')
        sch = cpht.schedules.create()
        sch.save()

        rand_id = lambda : random.randint(0, cpht.employees.count()-1)
        emp1 = cpht.employees.all()[rand_id()]
        emp2 = cpht.employees.all()[rand_id()]

        ts = emp1.template_schedules.create()
        ts.save()

        # create a template slot
        ts_range = sch.versions.first().workdays.count() // emp1.template_week_count
        print("EMPLOYEE:", emp1.name)
        print("EMPL TEMPLATE SIZE:", f"{emp1.template_week_count} weeks")
        print("TS RANGE:",ts_range)
        for i in range(sch.versions.first().workdays.count()):
            tss = ts.template_slots.create(
                    employee=emp1,
                    sd_id=i,
                    type='G',
                    )
            if i >= ts_range:
                tss.following = ts.template_slots.filter(sd_id=i % ts_range, employee=emp1).first()
            tss.save()
            print(tss,f"(mirrors: {tss.following.sd_id if tss.following else '-'})")

        for i in range(5):
            j = random.randint(0, ts_range)
            tss = ts.template_slots.filter(
                    employee=emp1,
                    sd_id=j).first()
            tss.type = 'D'
            tss.direct_shift = Shift.objects.filter(weekdays__contains=f"SMTWRFA"[i]).order_by('?').first()
            tss.save()
            print(f'TSS: {tss.sd_id} {tss.type} ',
                  f'TSS DIRECT TEMPLATE FOR: {tss.direct_shift}')




        print('#GTS:',emp1.template_slots.filter(type='G').count())
        print('#DTS:',emp1.template_slots.filter(type='D').count())

        self.assertEqual(emp1.template_slots.filter(type='G').count() + emp1.template_slots.filter(type='D').count(), emp1.template_slots.all().count())

        for ts in emp1.template_slots.filter(type='D'):
            print(ts.direct_shift, ts.sd_id, "SMTWRFA"[ts.sd_id % 7])






