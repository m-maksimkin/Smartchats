from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from . import forms


def account_index(request):
    return render(request, 'base.html')


class MyLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm


def sign_up_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:account_index")
    if request.method == "POST":
        form = forms.RegistrationForm(request.POST)
        # call form.save_user
        #run celery confirm email task
        ...
    else:
        form = forms.RegistrationForm()
    return render(request, "registration/sign_up.html", {"form": form})
