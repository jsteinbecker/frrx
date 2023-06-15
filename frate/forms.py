from django import forms
from .models import (Organization, Department, TimePhase, ShiftTraining,
                     Shift, Employee, Schedule,
                     BaseTemplateSlot, Slot)



class EmployeeCreateForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['name', 'department', 'start_date', 'shifts', 'fte']


class ShiftEditForm(forms.ModelForm):

    weekdays_set = forms.ChoiceField(choices=(('MTWRF','Weekdays Only'),('SMTWRFA','Every Day')))
    weekdays = forms.CharField(widget=forms.HiddenInput())


    class Meta:
        model = Shift
        fields = ('name', 'on_holidays', 'start_time', 'hours','weekdays', 'weekdays_set', 'verbose_name',
                  'department')
        readonly_fields = ('department')
        show_change_link = True
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'on_holidays': forms.CheckboxInput(attrs={'class':'form-control'}),
            'start_time': forms.TimeInput(attrs={'class':'form-control'}),
            'hours': forms.NumberInput(attrs={'class':'form-control'}),
            'verbose_name': forms.HiddenInput(),
            'department': forms.HiddenInput(),
        }




    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weekdays_set'].initial = self.instance.weekdays

    def clean(self):
        super().clean()
        data = self.cleaned_data
        if data['start_time']:
            self.instance.start_time = data['start_time']
        if data['name']:
            self.instance.verbose_name = data['name']
        if data['weekdays_set'] == 'MTWRF':
            self.instance.weekdays = 'MTWRF'
        elif data['weekdays_set'] == 'SMTWRFA':
            self.instance.weekdays = 'SMTWRFA'
        else:
            raise forms.ValidationError('Invalid weekday selection')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.save()
        return instance




