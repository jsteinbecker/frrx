from django import forms
from .models import (Organization, Department, TimePhase, ShiftTraining,
                     Shift, Employee, Schedule,
                     BaseTemplateSlot, Slot)



class EmployeeCreateForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['name', 'department', 'start_date', 'is_active', 'shifts']
        readonly_fields = ['is_active']


class ShiftEditForm(forms.ModelForm):

    weekdays_set = forms.Select(choices=(('MTWRF','Weekdays Only'), ('SMTWRFA', 'Weekdays & Weekends')))

    class Meta:
        model = Shift
        fields = ('name','on_holidays','weekdays','start_time','hours','phase')
        readonly_fields = ('slug','department','phase','weekdays')

    def __init__(self, *args, **kwargs):
        super(ShiftEditForm, self).__init__(*args, **kwargs)
        self.queryset = Shift.objects.all()
        self.fields['weekdays_set'].initial = 'MTWRF'




