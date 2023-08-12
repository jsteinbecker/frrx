from django.shortcuts import render, redirect
from .models import ProfileVerificationToken
from frate.models import Employee
from django.contrib.messages import warning


def profile(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    context = {
        'user': request.user,
        'profile': Employee.objects.get(user=request.user)
    }
    return render(request, 'profile/profile.html', context)


def generate_verif_token(request, dept, empl):
    employee = Employee.objects.get(department__slug=dept, slug=empl)
    if request.user.is_authenticated and request.user.is_superuser:
        if employee:
            if ProfileVerificationToken.objects.filter(employee=employee).exists():
                token = employee.verification_token
                token.delete()
            token = ProfileVerificationToken.objects.create(employee=employee, created_by=request.user)
            token.save()
            return render(request, 'profile/verif_token.html', {
                'token': token,
                'employee': employee})

    warning(request,
            'You are not authorized to access Verification Tokens. If you need this permission, '
            'talk to an administrator.')

    return redirect('dept:empl:detail', dept=dept, empl=empl)
