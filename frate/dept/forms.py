from frate.models import Department
from django import forms


class DeptEditForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ('name', 'verbose_name', 'schedule_week_length', 'initial_start_date')
