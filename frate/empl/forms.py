from django import forms
from frate.models import ShiftTraining, TimePhase, Department
from frate.sft.models import Shift
from frate.empl.models import Employee



STDHRS_CHOICES = (
        (0, 'Do Not Override Wanted Hours from FTE'),
        (10, '10 Hours'),
        (20, '20 Hours'),
        (30, '30 Hours'),
        (40, '40 Hours'),
        (50, '50 Hours'))


class EmployeeForm(forms.ModelForm):
    STREAK_CHOICES = (
        (2, '2 in-a-row'),
        (3, '3 in-a-row'),
        (4, '4 in-a-row'),
        (5, '5 in-a-row'),
        (6, '6 in-a-row'),
        (7, '7 in-a-row'),
        (8, '8 in-a-row'),
    )

    PTOHOURS_CHOICES = (
        (5, '5 hours'),
        (6, '6 hours'),
        (8, '8 hours'),
        (10, '10 hours'),
        (12, '12 hours'))


    phase_pref = forms.ModelChoiceField(queryset=TimePhase.objects.all())
    phase_pref.help_text = 'Select the time phase(s) that this employee prefers to work.'
    phase_pref.label = 'Time Phase Preference'

    streak_pref = forms.ChoiceField(choices=STREAK_CHOICES)
    streak_pref.help_text = 'Select the maximum number of consecutive days this employee prefers to work.'
    streak_pref.label = 'Streak Preference'

    pto_hours = forms.ChoiceField(choices=PTOHOURS_CHOICES)

    class Meta:
        model = Employee

        fields = ('name',
                  'department',
                  'fte',
                  'streak_pref',
                  'pto_hours',
                  'phase_pref',
                  'start_date',
                  'is_active',
                  'enrolled_in_inequity_monitoring',
                  'std_hours_override')

        widgets = {
            'phase_pref': forms.SelectMultiple(attrs={'class': 'select'}),
            'streak_pref': forms.SelectMultiple(attrs={'class': 'select2'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'pto_hours': forms.Select(attrs={'class': 'select2'}),
            'enrolled_in_inequity_monitoring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'std_hours_override': forms.Select(choices=STDHRS_CHOICES, attrs={'class': 'select2'}),}

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


class EmployeeCreateForm(forms.ModelForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all(),
                                        widget=forms.HiddenInput())

    fte = forms.DecimalField(max_digits=4, decimal_places=3, initial=1.0, min_value=0.0, max_value=1.0)
    fte.widget = forms.NumberInput(attrs={'class': 'form-control', 'step': 0.125})

    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Employee
        exclude = ('is_active', 'slug', 'first_name', 'last_name', 'initials', 'user')

    def __init__(self, *args, **kwargs):
        super(EmployeeCreateForm, self).__init__(*args, **kwargs)
        if self.initial:
            self.fields['shifts'].queryset = Shift.objects.filter(department=self.initial['department'])
