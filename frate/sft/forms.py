from frate.models import Shift
from frate.basemodels import Weekday
from django import forms


class ShiftInlineForm(forms.ModelForm):

    name = forms.CharField(max_length=100, required=False)
    verbose_name = forms.CharField(max_length=100, required=False)
    start_time = forms.TimeField()
    hours = forms.IntegerField()
    on_holidays = forms.BooleanField(required=False)
    weekdays = forms.ModelMultipleChoiceField(queryset=Weekday.objects.all(), required=False)
    slug = forms.HiddenInput()
    phase = forms.HiddenInput()
    department = forms.HiddenInput()

    class Meta:
        model = Shift
        fields = ('name', 'verbose_name', 'start_time', 'hours', 'on_holidays', 'weekdays', 'department')
        readonly_fields = ('department', )
        show_change_link = True
