from django import forms
from .models import (Organization, Department, TimePhase, ShiftTraining,
                     Shift, Employee, Schedule, Role, RoleSlot,
                     BaseTemplateSlot, Slot)



class EmployeeCreateForm(forms.ModelForm):

    department = forms.ModelChoiceField(queryset=Department.objects.all(),
                                        widget=forms.HiddenInput())
    fte = forms.DecimalField(max_digits=4, decimal_places=3, initial=1.0)
    fte.widget = forms.NumberInput(attrs={'class':'form-control', 'step':0.125})


    class Meta:
        model = Employee
        fields = ['name', 'department', 'start_date', 'shifts', 'fte','phase_pref','streak_pref']

    def __init__(self, *args, **kwargs):
        super(EmployeeCreateForm, self).__init__(*args, **kwargs)
        if self.initial:
            self.fields['shifts'].queryset = Shift.objects.filter(department=self.initial['department'])



class ShiftEditForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('name', 'verbose_name', 'on_holidays', 'start_time', 'hours',
                  'department', 'weekdays',)
        show_change_link = True
        widgets = {
            'name':        forms.TextInput(attrs={'class':'form-control'}),
            'on_holidays': forms.CheckboxInput(attrs={'class':'form-control'}),
            'start_time':  forms.TimeInput(attrs={'class':'form-control'}),
            'hours':       forms.NumberInput(attrs={'class':'form-control'}),
            'department':  forms.HiddenInput(),
            'is_active':   forms.CheckboxInput(attrs={'class':'form-control'}),
        }



class NewRoleForm(forms.ModelForm):

    class Meta:
        model = Role
        fields = ('department','name','week_count','max_employees')
        widgets = {
            'department': forms.HiddenInput(),
            'week_count': forms.RadioSelect(
                choices=[(1, '1 wk'), (2, '2 wks'), (3, '3 wks'),],
                attrs={'class': 'form-check-input flex flex-row flex-wrap gap-3 justify-center'}),
            }
        help_texts = {
            'role': 'Enter a name for this role.',
            'week_count': 'Enter the number of weeks per schedule',
            'max_employees': 'Enter the maximum number of employees that can be scheduled for this role.'
        }

class RTScheduleSlotFormPart1(forms.ModelForm):

    class Meta:
        model = RoleSlot
        fields = ('leader','sd_id','type','shifts')
        widgets = {
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
            'type': forms.Select(),
        }

class RTScheduleSlotFormPart2Direct(forms.ModelForm):

    shift = forms.ModelChoiceField(queryset=Shift.objects.all(),
                                      widget=forms.Select())

    class Meta:
        model = RoleSlot
        fields = ('shifts','leader','sd_id','type')
        widgets = {
            'shifts': forms.SelectMultiple(),
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
            'type': forms.HiddenInput(),
        }

class RTScheduleSlotFormPart2Rotating(forms.ModelForm):

    shifts = forms.ModelMultipleChoiceField(queryset=Shift.objects.all(),
                                            widget=forms.CheckboxSelectMultiple(),
                                            required=False)
    shifts.widget.attrs.update({'class': 'flex flex-row flex-wrap justify-start items-center gap-3'})

    class Meta:
        model = RoleSlot
        fields = ('shifts','leader','sd_id','type')
        widgets = {
            'shifts': forms.SelectMultiple(),
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
            'type': forms.HiddenInput(),
        }
















