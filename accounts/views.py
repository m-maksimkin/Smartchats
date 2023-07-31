from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from . import forms
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import EmailConfirmTokenGenerator
from django.utils.encoding import force_bytes
from django.urls import reverse
from .tasks import email_verify_task
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages


def account_index(request):
    return render(request, 'accounts/temp_index.html')


class MyLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm


def sign_up_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:account_index')
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            user = form.create_user()
            # call form.save_user
            # run celery confirm email task
            # redirect to confirmation email sent
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = EmailConfirmTokenGenerator().make_token(user)
            email = form.cleaned_data['email']
            url = request.build_absolute_uri(
                reverse('accounts:email_verify', args=(uidb64, token))
            )
            email_verify_task.delay(url, email)
            return render(request, 'accounts/mail/verify_email_sent.html')
    else:
        form = forms.RegistrationForm()
    return render(request, 'registration/sign_up.html', {'form': form})


def email_verify_view(request, uidb64, token):
    if request.user.is_authenticated:
        return redirect('accounts:account_index')
    pk = urlsafe_base64_decode(uidb64)
    user = get_object_or_404(get_user_model(), pk=pk)
    token_generator = EmailConfirmTokenGenerator()
    if token_generator.check_token(user, token):
        if user.email_verified:
            return render(request, 'accounts/mail/email_verify_link.html',
                          {'message': 'Данный аккаунт уже активирован'})
        else:
            user.email_verified = True
            user.is_active = True
            user.save()
            return render(request, 'accounts/mail/email_verify_link.html',
                          {'message': 'Аккаунт успешно активирован'})
    else:
        return render(request, 'accounts/mail/email_verify_link.html',
                      {'message': 'Данная ссылка больше не действительна'})


def signup_redirect_view(request):
    messages.error(request,
                   'Что-то пошло не так, возможно этот аккаунт уже зарегистрирован')
    return redirect('accounts:login')


def account_inactive_view(request):
    messages.error(request,
                   'Данный аккаунт временно заблокирован.')
    return redirect('accounts:login')

