from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from frate.forms import RegisterForm
from frate.models import Employee, Organization, ProfileVerificationToken
from django.contrib import messages


def profile(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if not Employee.objects.filter(user=request.user).exists():
        if request.user.is_superuser:
            unlinked = Employee.objects.filter(user=None)

            if request.method == 'POST':
                user = request.user
                employee = Employee.objects.get(slug=request.POST['employee'])
                employee.user = user
                employee.save()

                messages.success(request, 'Employee linked successfully!')
                return redirect('/profile/')

            return render(request, 'profile/link-employee.html', {'unlinked': unlinked})
        else:
            return render(request, 'profile/employee-not-found.html')
    context = {
        'user': request.user,
        'profile': Employee.objects.get(user=request.user)
    }
    return render(request, 'profile/profile.html', context)


def logout_view(request):
    logout(request)
    return redirect('/login/')


def register(request):

    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            org = form.cleaned_data['organization']
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            token = form.cleaned_data['verify_token']

            user = User.objects.create_user(username=username, password=password)
            user.save()

            emp = Employee.objects.get(department__organization=org, verification_token=token)
            emp.user = user
            emp.save()

            token.delete()

            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/profile/')

    context = {'form': form}

    return render(request, 'profile/register.html', context)



