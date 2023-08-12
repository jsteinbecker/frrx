from frate.models import *
from django import forms

from frate.role.models import Role


class RoleInitForm(forms.ModelForm):

    role = forms.CharField(max_length=50)
    week_count = forms.IntegerField()
    max_employees = forms.IntegerField()
    department = forms.ModelChoiceField(queryset=Department.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Role
        fields = ('department','role','week_count','max_employees')


class RoleSlotTypeSwitcherForm(forms.Form):

    DISPLAY_CLASSES = (
        ('D', "bg-sky-300 bg-opacity-30 border border-sky-500"),
        ('R', "bg-indigo-300 bg-opacity-30 border border-indigo-500"),
        ('O', "bg-amber-600 bg-opacity-30 border border-amber-800"),
        ('G', "bg-green-300 bg-opacity-30 border border-green-500"),
    )

    role_slot = forms.ModelChoiceField(queryset=RoleSlot.objects.all(), widget=forms.HiddenInput())
    progress_type = forms.CheckboxInput()

    def __init__(self, *args, **kwargs):
        super(RoleSlotTypeSwitcherForm, self).__init__(*args, **kwargs)
        self.fields['role_slot'].initial = kwargs['initial']['role_slot']
        self.fields['type'].initial = kwargs['initial']['role_slot'].type

    def save(self):
        role_slot = self.cleaned_data['role_slot']
        role_slot.type = self.cleaned_data['type']
        if self.cleaned_data['progress_type']:
            if role_slot.type == 'D':
                role_slot.type = 'R'
            elif role_slot.type == 'R':
                role_slot.type = 'G'
            elif role_slot.type == 'G':
                role_slot.type = 'O'
            elif role_slot.type == 'O':
                role_slot.type = 'D'
        role_slot.save()
