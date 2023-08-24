from frate.models import Department
from django import forms


class DeptEditForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ('name', 'verbose_name', 'schedule_week_length', 'initial_start_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'text-xl font-bold'}),
            'schedule_week_length': forms.RadioSelect(
                    choices=[(1, '1 week'),
                             (2, '2 weeks'),
                             (4, '4 weeks'),
                             (6, '6 weeks'),
                             (8, '8 weeks')],
                    attrs={'class': 'form-check-input flex flex-row flex-wrap gap-3 justify-center'}),
            'initial_start_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'name': 'The name of the department',
            'verbose_name': 'The name of the department as it should appear in the schedule',
            'schedule_week_length': 'The length of a schedule week',
            'initial_start_date': 'The date of the first schedule. Based on this date, subsequent schedules '
                                  'will be generated at the appropriate interval.'
        }

