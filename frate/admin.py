from django.contrib import admin
from django import forms

# Register your models here.

from .models import Organization, Department, TimePhase, Shift, Employee, ShiftTraining, Schedule

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    class DepartmentInline(admin.TabularInline):
        model = Department
        extra = 0
        fields = ('name', 'verbose_name', 'organization', 'schedule_week_length', 'initial_start_date')

        show_change_link = True



    fieldsets = (
        (None, {
            'fields': ('name', 'verbose_name')
        }),
        ('Indexing', {
            'fields': ('slug',)
        }),
    )

    list_display = ('name','verbose_name')
    list_filter = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')
    ordering = ('name', 'verbose_name')
    readonly_fields = ('slug',)
    inlines = [DepartmentInline]

class ShiftInlineForm(forms.BaseModelForm):

        weekday_scheduling        = forms.ChoiceField(choices=(('MTWRF','Weekdays Only'),
                                                               ('SMTWRFA','Every Day')))
        weekday_scheduling.widget = forms.Select(attrs={'class':'form-control'})

        class Meta:
            model = Shift
            fields = ('name', 'on_holidays', 'start_time', 'hours', 'phase', 'weekday_scheduling')
            readonly_fields = ('slug','department','phase')
            show_change_link = True


        def clean(self):
            super().clean()
            data = self.cleaned_data


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

        fieldsets = (
            (None, {
                'fields': ('name','start_time', 'hours',)
            }),
            ('Department', {
                'fields': ('department','on_holidays'),
            }),
            ('Indexing', {
                'fields': ('slug','phase')
            }),
        )

        list_display = ('name','on_holidays', 'start_time', 'hours', 'phase')
        list_filter = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
        search_fields = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
        ordering = ('name', 'on_holidays', 'start_time', 'hours', 'phase')
        readonly_fields = ('slug','phase')




        def save_model(self, request, obj, form, change):
            super().save_model(request, obj, form, change)





@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    class Media:
        css = {
            'all': ('/static/css/admin.css',)
        }

    class ShiftInline(admin.TabularInline):

        from .forms import ShiftEditForm
        model = Shift
        extra = 0
        show_change_link = True
        form  = ShiftEditForm
        fieldsets = (
            (None, {
                'fields': ('name', 'on_holidays', 'start_time', 'hours')
            }),
        )
        classes = ('grp-collapse grp-closed',)


    class ScheduleInline(admin.TabularInline):
        model = Schedule
        extra = 0
        fieldsets = (
            (None, {
                'fields': ('year','n', 'status', ),
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
            'fields': ('image', 'icon_id'),
        }),
    )


    list_display    = ('name','verbose_name')
    list_filter     = ('name', 'verbose_name')
    search_fields   = ('name', 'verbose_name')
    ordering        = ('name', 'verbose_name')
    readonly_fields = ('slug',)
    inlines         = [ShiftInline, ScheduleInline]



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    class ShiftTrainingInline(admin.TabularInline):
        model = ShiftTraining
        extra = 0
        fields = ('shift', 'is_active')
        show_change_link = True

    fieldsets = (
        (None, {
            'fields': ('name', 'department',)
        }),
        ('Indexing', {
            'fields': ('slug','first_name', 'last_name', 'initials'),
            'classes': ('grp-collapse grp-closed',),
            'description': 'These fields are automatically generated from the name field.'
        }),
        ('Department Role Details', {
            'fields': ('fte','start_date', 'shifts'),
        }),
    )
    readonly_fields = ('slug','first_name', 'last_name', 'initials','shifts')

    list_display = ('name','department','initials')
    list_filter = ('name', 'department')
    search_fields = ('name', 'department')
    ordering = ('name', 'department')
    inlines = [ShiftTrainingInline]

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('status',)
        }),
        ('Indexing', {
            'fields': ('year', 'n', 'department', 'slug','start_date'),
            'classes': ('grp-collapse grp-closed',),
        }),
    )
    readonly_fields = ('year', 'n', 'department', 'slug','start_date')

    list_display = ('year', 'n', 'department', 'status')
    list_filter = ('year', 'n', 'department', 'status')
    search_fields = ('year', 'n', 'department', 'status')
    ordering = ('year', 'n', 'department', 'status')
