from django import forms
from frate.models import Employee, Shift, ShiftTraining


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



