from django import forms
from django.contrib.auth.models import User

from .models import (RoleSlot, Organization)
from .profile.models import ProfileVerificationToken
from .role.models import Role
from .sft.models import Shift


class RegisterForm(forms.Form):
    organization = forms.CharField(max_length=32)
    username = forms.CharField(max_length=32)
    name = forms.CharField(max_length=32)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=32, widget=forms.PasswordInput, label='Confirm Password')
    verify_token = forms.CharField(max_length=32)


    def clean_organization(self):
        org = self.cleaned_data['organization']
        if not Organization.objects.filter(name__iexact=org.strip()).exists():
            raise forms.ValidationError('Organization not found.')
        return org

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists')
        return username

    def clean_password2(self):
        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']
        if password != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def clean_verify_token(self):
        token = self.cleaned_data['verify_token']
        if not ProfileVerificationToken.objects.filter(token=token).exists():
            raise forms.ValidationError('Invalid token')
        return token

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        if 'organization' in cleaned_data:
            org = Organization.objects.get(name__iexact=cleaned_data['organization'])
            cleaned_data['organization'] = org
        if 'verify_token' in cleaned_data:
            token = ProfileVerificationToken.objects.get(token=cleaned_data['verify_token'])
            cleaned_data['verify_token'] = token
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=32)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username does not exist')
        return username

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        if 'usernasme' in cleaned_data:
            username = cleaned_data['username']
            cleaned_data['username'] = User.objects.get(username=username)
        return cleaned_data


class NewRoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ('department', 'name', 'week_count', 'max_employees')
        widgets = {
            'department': forms.HiddenInput(),
            'week_count': forms.RadioSelect(
                choices=[(1, '1 wk'), 
                         (2, '2 wks'), 
                         (3, '3 wks')],
                attrs={'class': 'form-check-input flex '
                                'flex-row flex-wrap gap-3 '
                                'justify-center'}),
        }
        help_texts = {
            'role': 'Enter a name for this role.',
            'week_count': 'Enter the number of weeks per schedule',
            'max_employees': 'Enter the maximum number of employees that can be scheduled for this role.'
        }


class RTScheduleSlotFormPart1(forms.ModelForm):
    class Meta:
        model = RoleSlot
        fields = ('leader', 'sd_id', 'shifts')
        widgets = {
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
        }


class RTScheduleSlotFormPart2Direct(forms.ModelForm):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(),
                                   widget=forms.Select())

    class Meta:
        model = RoleSlot
        fields = ('shifts', 'leader', 'sd_id')
        widgets = {
            'shifts': forms.SelectMultiple(),
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
        }


class RTScheduleSlotFormPart2Rotating(forms.ModelForm):
    shifts = forms.ModelMultipleChoiceField(queryset=Shift.objects.all(),
                                            widget=forms.CheckboxSelectMultiple(),
                                            required=False)
    shifts.widget.attrs.update({'class': 'flex flex-row flex-wrap justify-start items-center gap-3'})

    class Meta:
        model = RoleSlot
        fields = ('shifts', 'leader', 'sd_id')
        widgets = {
            'shifts': forms.SelectMultiple(),
            'leader': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
        }
