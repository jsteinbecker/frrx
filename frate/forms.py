from django import forms
from .models import (Organization, Department, TimePhase, ShiftTraining,
                     Shift, Employee, Schedule,
                     BaseTemplateSlot, Slot)



class EmployeeCreateForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['name', 'department', 'start_date', 'shifts', 'fte']


class ShiftEditForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('name', 'on_holidays', 'start_time', 'hours',
                  'department', 'weekdays')
        show_change_link = True
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'on_holidays': forms.CheckboxInput(attrs={'class':'form-control'}),
            'start_time': forms.TimeInput(attrs={'class':'form-control'}),
            'hours': forms.NumberInput(attrs={'class':'form-control'}),
            'department': forms.HiddenInput(),
        }









