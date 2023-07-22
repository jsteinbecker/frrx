from frate.sft.models import Shift
from frate.basemodels import Weekday
from django import forms



class ShiftEditForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('name', 'verbose_name', 'on_holidays', 'start_time', 'hours',
                  'department', 'weekdays','department','is_active')
        show_change_link = True
        widgets = {
            'name':        forms.TextInput(attrs={'class':'form-control'}),
            'on_holidays': forms.CheckboxInput(attrs={'class':'form-control'}),
            'start_time':  forms.TimeInput(attrs={'class':'form-control', 'type':'time'}),
            'hours':       forms.NumberInput(attrs={'class':'form-control'}),
            'department':  forms.HiddenInput(),
            'is_active':   forms.HiddenInput(),
        }
        help_texts = {
            'verbose_name': 'A full, descriptive name for the shift.',
            'on_holidays': 'If your organization uses a downstaffing model on holidays, indicate whether this shift is affected.',
            'hours': 'The number of payroll eligible hours for this shift.',
            'weekdays': 'Indicate which days are typically staffed by this shift.',
        }
