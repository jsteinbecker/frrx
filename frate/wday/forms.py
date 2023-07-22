from django import forms
from django.db.models import Q
from frate.models import PtoRequest, Department
from frate.wday.models import Workday
from frate.empl.models import Employee


class AddPtoRequestForm(forms.Form):

    workday     = forms.ModelChoiceField(queryset=Workday.objects.all(), widget=forms.HiddenInput())
    department  = forms.ModelChoiceField(queryset=Department.objects.all(), widget=forms.HiddenInput())
    employee    = forms.ModelChoiceField(queryset=Employee.objects.all())

    def __init__(self, *args, **kwargs):
        super(AddPtoRequestForm, self).__init__(*args, **kwargs)
        if 'workday' in self.initial:
            date = self.initial['workday'].date
        if 'department' in self.initial:
            self.fields['employee'].queryset = Employee.objects.filter(
                                                department=self.initial['department']).exclude(
                                                pto_requests__date=date)

    def save(self):
        workday = self.cleaned_data['workday']
        employee = self.cleaned_data['employee']
        pto_request = PtoRequest(date=workday.date, employee=employee)
        pto_request.save()
        return pto_request

