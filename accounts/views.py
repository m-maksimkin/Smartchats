from django.shortcuts import render
from django.contrib.auth.views import LoginView
from . import forms


def account_index(request):
    return render(request, 'base.html')


class MyLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm