from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from . import forms
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import EmailConfirmTokenGenerator
from django.utils.encoding import force_bytes


def account_index(request):
    return render(request, 'base.html')


class MyLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm


def sign_up_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:account_index")
    if request.method == "POST":
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            user = form.create_user()
            # call form.save_user
            # run celery confirm email task
            # redirect to confirmation email sent
            uid64 = urlsafe_base64_encode(force_bytes(user.id))
            token = EmailConfirmTokenGenerator().make_token(user)
            print(int(urlsafe_base64_decode(uid64)))
            return HttpResponse(uid64 + ' ' + token + '  ')
    else:
        form = forms.RegistrationForm()
    return render(request, "registration/sign_up.html", {"form": form})
