from django import forms
from frate.models import Employee, Shift, ShiftTraining, TimePhase


class EmployeeForm(forms.ModelForm):

    STREAK_CHOICES = (
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
    )

    phase_pref = forms.ModelChoiceField(queryset=TimePhase.objects.all())
    phase_pref.help_text = 'Select the time phase(s) that this employee prefers to work.'
    phase_pref.label = 'Time Phase Preference'

    streak_pref = forms.ChoiceField(choices=STREAK_CHOICES)
    streak_pref.help_text = 'Select the maximum number of consecutive days this employee prefers to work.'
    streak_pref.label = 'Streak Preference'

    class Meta:
        model = Employee
        fields = ('name','department','fte',
                  'streak_pref','pto_hours','phase_pref',
                  'start_date','is_active','enrolled_in_inequity_monitoring',)
        widgets = {
            'phase_pref': forms.SelectMultiple(attrs={'class': 'select2'}),
            'streak_pref': forms.SelectMultiple(attrs={'class': 'select2'}),
        }
        help_texts = {
            'name': 'Enter the name of the employee.',
            'department': 'Select the department that this employee belongs to.',
            'fte': 'Enter the FTE of this employee.',
            'streak_pref': 'Select the maximum number of consecutive days this employee prefers to work.',
            'pto_hours': 'Enter the number of PTO hours this employee has.',
            'phase_pref': 'Select the time phase(s) that this employee prefers to work.',
            'start_date': 'Enter the start date of this employee.',
            'is_active': 'Select whether this employee is active or not.',
            'enrolled_in_inequity_monitoring': 'Select whether this employee is enrolled in inequity monitoring.',
        }

TRAINING_CHOICES = (
    ('AV', 'Available'),
    ('UA', 'Unavailable'),
    ('UT', 'Untrained'),
)

class TrainingForm(forms.Form):

    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    training = forms.ChoiceField(choices=TRAINING_CHOICES)

    class Meta:
        fields = ('employee', 'shift', 'training')
        widgets = {
            'employee': forms.HiddenInput(),
            'shift': forms.HiddenInput(),
            'training': forms.Select(choices=TRAINING_CHOICES),
        }

    def save(self, commit=True):
        employee = self.cleaned_data['employee']
        shift = self.cleaned_data['shift']
        training = self.cleaned_data['training']
        if training == 'UT':
            if employee.shifttraining_set.filter(shift=shift).exists():
                employee.shifttraining_set.filter(shift=shift).delete()
        else:
            if training == 'AV':
                if employee.shifttraining_set.filter(shift=shift).exists():
                    tr = employee.shifttraining_set.filter(shift=shift).first()
                    tr.is_active = True
                    tr.save()
                else:
                    ShiftTraining.objects.create(employee=employee, shift=shift, is_active=True)
            elif training == 'UA':
                if employee.shifttraining_set.filter(shift=shift).exists():
                    tr = employee.shifttraining_set.filter(shift=shift).first()
                    tr.is_active = False
                    tr.save()
                else:
                    ShiftTraining.objects.create(employee=employee, shift=shift, is_active=False)
        return super().save(commit=commit)


        super().save(commit=commit)



