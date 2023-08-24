from django.contrib import admin
from django import forms
from django.db.models import Sum

# Register your models here.

from .models import (Organization, Department, TimePhase,
                     ShiftTraining,
                     Slot, Weekday,
                     RoleSlot, RoleLeaderSlot)
from .pto.models import PtoRequest
from .sch.models import Schedule
from .role.models import Role
from .wday.models import Workday
from .sft.models import Shift
from .empl.models import Employee
from .ver.models import Version
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    readonly_fields = ('slug', 'first_name', 'last_name', 'department')
    verbose_name_plural = "employee"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = [EmployeeInline]


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



@admin.register(Weekday)
class WeekdayAdmin(admin.ModelAdmin):
    fields = ('name', 'abvr', 'short', 'n')
    list_display = ('name', 'abvr', 'short', 'n')
    list_editable = ('short', 'n')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    class DepartmentInline(admin.TabularInline):
        model = Department
        extra = 0
        fields = ('name', 'verbose_name', 'schedule_week_length', 'initial_start_date')
        show_change_link = True

    class PhaseInline(admin.TabularInline):
        model = TimePhase
        extra = 0
        fields = ('name', 'verbose_name', 'end_time', 'rank', 'organization')

    fieldsets = (
        (None, {
            'fields': ('name', 'verbose_name')
        }),
        ('Indexing', {
            'fields': ('slug',)
        }),
    )

    list_display = ('name', 'verbose_name')
    list_filter = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')
    ordering = ('name', 'verbose_name')
    readonly_fields = ('slug',)
    inlines = [PhaseInline]


class ShiftInlineForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ('name', 'on_holidays', 'hours', 'phase', 'weekdays')
        readonly_fields = ('slug', 'department', 'phase')
        show_change_link = True


@admin.register(TimePhase)
class TimePhaseAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'verbose_name', 'end_time', 'rank')
        }),
        ('Indexing', {
            'fields': ('icon_id', 'organization', 'color')
        }),
    )

    list_display = ('name', 'verbose_name', 'end_time', 'rank', 'icon_id', 'color')
    list_filter = ('name', 'verbose_name', 'end_time', 'rank')
    search_fields = ('name', 'verbose_name', 'end_time', 'rank')
    ordering = ('rank',)
    list_display_links = ('name',)
    list_editable = ('verbose_name', 'end_time', 'icon_id', 'color')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'start_time', 'hours')
        }),
        ('Department', {
            'fields': ('department', 'on_holidays', 'adjacent_rotating_slot_pref')
        }),
        ('Indexing', {
            'fields': ('slug', 'phase'),
            'classes': ('collapse',)
        }),
    )

    list_display = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
    list_filter = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
    search_fields = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
    ordering = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
    readonly_fields = ('slug', 'phase')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    fields = ('department', 'name', 'week_count', 'description')

    class RoleSlotInline(admin.TabularInline):

        model = RoleLeaderSlot
        fieldset = ((None, {'fields': ('sd_id', 'type', 'weekday',),
                            'classes': ('grp-collapse grp-closed',)}),
                    ('Shift', {'fields': ('shifts_set',),
                               'classes': ('grid grid-cols-5')}))
        show_change_link = False
        readonly_fields = ('sd_id', 'weekday')
        extra = 0
        classes = ('grp-collapse grp-closed',)

        def weekday(self, obj):
            if obj.sd_id:
                return "Sun Mon Tue Wed Thu Fri Sat".split(" ")[obj.sd_id % 7 - 1] + f"-{obj.sd_id // 7 + 1}"
            else:
                return None

        def get_formset(self, request, obj=None, **kwargs):
            formset = super().get_formset(request, obj, **kwargs)

            # Create a new class that changes the widget for the 'shifts' field
            class FormWithShiftsCheckbox(formset.form):
                shifts = forms.ModelMultipleChoiceField(
                    queryset=Shift.objects.filter(department=obj.department),
                    widget=forms.CheckboxSelectMultiple,
                    required=False
                )

            # Replace the form with our custom form
            formset.form = FormWithShiftsCheckbox
            return formset

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            self.inlines = []
        else:
            self.inlines = [self.RoleSlotInline]
        return super().get_form(request, obj, **kwargs)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('/static/css/admin.css',)
        }

    class ShiftInline(admin.TabularInline):
        model = Shift
        extra = 0
        show_change_link = True
        show_full_result_count = True
        exclude = ('slug', 'verbose_name')
        classes = ('grp-collapse grp-open',)

    class ScheduleInline(admin.TabularInline):
        model = Schedule
        extra = 0
        fieldsets = (
            (None, {
                'fields': ('year', 'n', 'status',),
                'classes': ('grp-collapse grp-closed',),
            }),
        )
        show_change_link = True
        classes = ('grp-collapse grp-closed',)

    fieldsets = (
        (None, {
            'fields': ('name', 'verbose_name', 'organization', 'schedule_week_length', 'initial_start_date')
        }),
        ('Indexing', {
            'fields': ('slug',)
        }),
        ('Image', {
            'fields': ('image', 'icon_id')
        }),
    )

    list_display = ('name', 'verbose_name')
    list_filter = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')
    readonly_fields = ('slug',)
    inlines = [ShiftInline, ScheduleInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    class ShiftTrainingInline(admin.TabularInline):
        model = ShiftTraining
        extra = 0
        fields = ('shift', 'is_active', 'rank')
        show_change_link = True
        sortable_field_name = 'rank'
        sortable_by = ('rank',)

    class ScheduleInline(admin.TabularInline):
        model = Schedule.employees.through
        extra = 0
        fields = ('pd_id', 'hours', 'status')
        show_change_link = True

        def employee_hours_per_period(self, obj):
            pd_hours_list = []
            for period in set(obj.schedules.all().values_list('pd_id', flat=True)):
                pd_hrs = obj.schedules.filter(pd_id=period).aggregate(Sum('hours'))['hours__sum']
                pd_hours_list.append(pd_hrs)
            return pd_hours_list

    fieldsets = (
        (None, {
            'fields': ('name', 'department', 'user')
        }),
        ('Indexing', {
            'fields': ('slug', 'first_name', 'last_name', 'initials'),
            'classes': ('grp-collapse grp-closed',),
            'description': 'These fields are automatically generated from the name field.'
        }),
        ('Department Role Details', {
            'fields': ('fte', 'start_date', 'shifts', 'is_active', 'phase_pref', 'enrolled_in_inequity_monitoring'),
        }),
    )
    readonly_fields = ('slug', 'first_name', 'last_name', 'initials', 'shifts')

    list_display = ('name', 'department', 'initials', 'phase_pref',
                    'enrolled_in_inequity_monitoring',
                    'is_active', 'pto_hours', 'fte', 'start_date')
    list_filter = ('name', 'department')
    list_editable = ('phase_pref', 'pto_hours',)
    search_fields = ('name', 'department')
    ordering = ('name', 'department')
    inlines = [ShiftTrainingInline, ]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('department', 'status',)
                }),
        ('Indexing', {'fields': ('year', 'n', 'slug', 'start_date'),
                      'classes': ('grp-collapse grp-closed',),
                      }),
    )
    readonly_fields = ('display', 'year', 'n', 'slug', 'start_date')

    list_display = ('display', 'year', 'n', 'department', 'status', 'start_date')
    list_filter = ('year', 'n', 'department', 'status')
    search_fields = ('year', 'n', 'department', 'status')
    ordering = ('year', 'n', 'department', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields + ('status',)
        return self.readonly_fields

    @classmethod
    def display(cls, obj):
        return f"{obj.year} Sch #{obj.n} {obj.department.name} ({obj.status})"
