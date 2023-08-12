from frate.models import Department
from django import forms


class DeptEditForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ('name', 'verbose_name', 'schedule_week_length', 'initial_start_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'text-xl font-bold'}),
            'schedule_week_length': forms.RadioSelect(
                    choices=[(1, '1 wk'),
                             (2, '2 wks'),
                             (4, '4 wks'),
                             (6, '6 wks'),
                             (8, '8 wks')],
                    attrs={'class': 'form-check-input flex flex-row flex-wrap gap-3 justify-center'}),
            'initial_start_date': forms.DateInput(attrs={'type': 'date'}),
        }
