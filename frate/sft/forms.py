from frate.models import Shift
from frate.basemodels import Weekday
from django import forms


class ShiftInlineForm(forms.ModelForm):

    class Meta:
        model = Shift
        exclude = ()
        readonly_fields = ('department', )
        show_change_link = True

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('hours') > 12:
            raise forms.ValidationError("Shifts cannot be longer than 12 hours.")
        return cleaned_data


