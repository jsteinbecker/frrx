import datetime
import json

from django.contrib import messages
from django.db.models import Count
from django.forms import formset_factory
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render

from frate.models import Department
from .forms import TrainingForm, EmployeeForm, EmployeeCreateForm
from .models import Employee
from ..sch.models import Schedule
from ..sft.models import Shift


def empl_list(request, dept):
    dept = Department.objects.get(slug=dept)
    empls = Employee.objects.filter(department=dept)

    for empl in empls:
        empl.save()

    return render(
        request,
        "empl/list.html",
        {"employees": empls, "dept": dept, "title": "Employees"},
    )


def empl_search(request, dept):
    dept = Department.objects.get(slug=dept)
    search = request.GET.get("q")
    empls = Employee.objects.filter(department=dept, name__icontains=search)
    if not empls:
        empls = Employee.objects.filter(department=dept, slug__icontains=search)
    return JsonResponse({"employees": list(empls.values_list("name", flat=True))})


def empl_inequity_monitoring(request, dept):
    dept = Department.objects.get(slug=dept)
    empls = Employee.objects.filter(
        department=dept, enrolled_in_inequity_monitoring=True
    )

    if len(empls) == 0:
        pct_enrolled = 0
    else:
        pct_enrolled = int(empls.count() / dept.employees.count() * 100)

    return render(request,"empl/inequity.html",
        {
            "employees": empls,
            "dept": dept,
            "title": "Inequity Monitoring",
            "count": empls.count(),
            "pct_enrolled": pct_enrolled,
        },
    )


def empl_new(request, dept):
    dept = Department.objects.get(slug=dept)
    form = EmployeeCreateForm(initial={"department": dept})
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/department/" + dept.slug + "/employee/")
    return render(request,"empl/new.html",
        {"form": form, "dept": dept.name, "title": "New Employee"},
    )


def empl_detail(request, dept, empl):
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)
    profile = empl.user

    if request.user != profile:
        if not request.user.is_superuser:
            editable = False
        else:
            editable = True
    else:
        editable = True

    return render(
        request,
        "empl/detail.html",
        {"employee": empl, "dept": dept, "profile": profile},
    )


def empl_edit(request, dept, empl):
    form = EmployeeForm(instance=Employee.objects.get(slug=empl))
    empl = Employee.objects.get(slug=empl, department__slug=dept)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=empl)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("../")
    return render(
        request,
        "empl/forms/edit.html",
        {"form": form, "employee": empl, "title": "Edit Employee"},
    )


def empl_templates(request, dept, empl):
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)

    alt_template_week_count = 3 if empl.template_week_count == 2 else 2

    template_sch = empl.template_schedules.get_or_create(status="A")[0]
    template_sch.save()

    return render(
        request,
        "empl/templating.html",
        {
            "employee": empl,
            "alt_week_count": "Change to {} weeks".format(alt_template_week_count),
            "dept": dept,
            "title": "Employee Templates",
            "template_slots": template_sch.template_slots.filter(
                following__isnull=True
            ).annotate(rotating_shifts_count=Count("rotating_shifts")),
            "template_sch": template_sch,
        },
    )


def get_options(request, dept, empl):
    """For a"""
    sd_ids = request.GET.get("sdids").split(",")
    sd_ids = [int(sd_id) for sd_id in sd_ids]
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)

    weekdays = []
    for sd_id in sd_ids:
        wd = "SMTWRFA"[sd_id % 7 - 1]
        if wd not in weekdays:
            weekdays.append(wd)
    weekdays = set(weekdays)
    print("WEEKDAYS", weekdays)

    allowed = []
    for shift in empl.shifts.all():
        if all([wd in shift.weekdays for wd in weekdays]):
            print(shift)
            allowed.append(shift.pk)

    if allowed:
        shifts = Shift.objects.filter(pk__in=allowed)
    else:
        shifts = Shift.objects.none()

    return render(
        request,
        "empl/template-slots/ts-form.html",
        {"shifts": shifts, "dept": dept, "empl": empl, "sdids": sd_ids},
    )


def empl_templates_update(request, dept, empl):
    if request.method == "POST":
        sd_ids = json.loads(request.POST.get("sdids"))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)
        shift = Shift.objects.get(slug=request.POST.get("shift"))

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = shift
                ts.type = "D"
                ts.save()

        return HttpResponseRedirect(
            f"/department/{dept.slug}/employee/{empl.slug}/templates/"
        )


def empl_templates_update_to_rotating(request, dept, empl):
    if request.method == "POST":
        sd_ids = json.loads(request.POST.get("sdids"))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)
        shifts = Shift.objects.filter(slug__in=request.POST.getlist("shifts"))

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.rotating_shifts.set(shifts)
                ts.type = "R"
                ts.save()

        return HttpResponseRedirect(
            f"/department/{dept.slug}/employee/{empl.slug}/templates/"
        )


def empl_templates_update_to_tdo(request, dept, empl):
    if request.method == "POST":
        sd_ids = json.loads(request.POST.get("sdids"))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.type = "O"
                ts.save()
                print("SAVED", ts)
        return HttpResponseRedirect(
            f"/department/{dept.slug}/employee/{empl.slug}/templates/"
        )


def empl_templates_to_generic(request, dept, empl):
    if request.method == "POST":
        sd_ids = json.loads(request.POST.get("sdids"))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.type = "G"
                ts.save()
                print("SAVED", ts)
        return HttpResponseRedirect(
            f"/department/{dept.slug}/employee/{empl.slug}/templates/"
        )


def add_pto_req(request, dept, empl):
    if request.method == "POST":
        print(request.POST)
        day = int(request.POST.get("day"))
        month = int(request.POST.get("month"))
        year = int(request.POST.get("year"))
        date = datetime.date(year, month, day)
        empl = Employee.objects.get(slug=empl, department__slug=dept)
        empl.pto_requests.create(date=date)
        messages.success(request, f"PTO Request Added for {date.strftime('%m/%d/%Y')}")
        return HttpResponseRedirect(empl.url)
    return HttpResponse("ERROR")


def update_trainings(request, dept, empl):
    employee = Employee.objects.get(slug=empl, department__slug=dept)
    shifts = employee.department.shifts.all()
    initial = []
    for shift in shifts:
        if employee.shifttraining_set.filter(is_active=True, shift=shift).exists():
            trained = "AV"
        elif employee.shifttraining_set.filter(is_active=False, shift=shift).exists():
            trained = "UA"
        else:
            trained = "UT"
        initial.append(
            {
                "employee": employee,
                "shift": shift,
                "training": trained,
            }
        )
    ShiftTrainingFormset = formset_factory(TrainingForm, extra=0)
    formset = ShiftTrainingFormset(initial=initial)
    if request.method == "POST":
        formset = ShiftTrainingFormset(request.POST)
        if formset.is_valid():
            for form in formset:
                shift = form.cleaned_data["shift"]
                training = form.cleaned_data["training"]
                if training == "AV":
                    tr = employee.shifttraining_set.get_or_create(shift=shift)[0]
                    tr.is_active = True
                    tr.save()
                elif training == "UA":
                    tr = employee.shifttraining_set.get_or_create(shift=shift)[0]
                    tr.is_active = False
                    tr.save()
                else:
                    employee.shifttraining_set.filter(shift=shift).delete()
            messages.success(request, f"Trainings Updated for {employee}")
        return HttpResponseRedirect(employee.url)
    return render(
        request, "empl/forms/training.html", {"formset": formset, "employee": employee}
    )


def empl_sort_shifts(request, dept, empl):
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl, department=dept)

    trainings = empl.shifttraining_set.all()

    if len(trainings) == 1:
        return render(request, "empl/forms/sort-ineligible.html", {'empl': empl})

    if request.method == "POST":
        print(request.POST)
        shift_ids = request.POST.getlist("shifts")
        i = 0
        for shift in shift_ids:
            train = trainings.get(pk=shift)
            train.rank = i
            train.save()
            i += 1

        messages.success(request, f"Shift Preferences Updated for {empl}")
        return HttpResponseRedirect(empl.url)

    return render(
        request, "empl/forms/sort.html", {"empl": empl, "trainings": trainings}
    )


class Utils:
    @staticmethod
    def validate_date(request, dept, empl):
        print(request.META["QUERY_STRING"])

        if request.method == "GET":
            day = request.GET.get("day")
            month = request.GET.get("month")
            year = request.GET.get("year")

            print(year, month, day)

            day = int(day) if day else None
            month = int(month) if month else None
            year = int(year) if year else None

            if not all([day, month, year]):
                return HttpResponse("ERROR")

            try:
                date = datetime.date(year, month, day)
                return HttpResponse("VALID")
            except:
                pass

            empl = Employee.objects.get(slug=empl, department__slug=dept)

        return HttpResponse("ERROR")

    @staticmethod
    def swap_template_week_ct(request, dept, empl):
        empl = Employee.objects.get(slug=empl, department__slug=dept)
        week_ct = empl.template_week_count
        if week_ct == 2:
            empl.template_week_count = 3
        else:
            empl.template_week_count = 2
        empl.save()
        return HttpResponseRedirect(empl.url + "templates/")

    @staticmethod
    def get_employees_period_hours(request, dept, empl, sch, ver, prd):
        dept = Department.objects.get(slug=dept)
        schedule = Schedule.objects.get(slug=sch, department=dept)
        version = schedule.versions.get(n=ver)
        period = version.periods.get(pd_id=prd, employee__slug=empl)
        period.save()
        return HttpResponse(period.hours)
