from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = (
            "Пожалуйста ведите правильный адрес почты и пароль."
        )

# class EmailAuthenticationForm(forms.Form):
#     email = forms.EmailField(label="Email")
#     password = forms.CharField(widget=forms.PasswordInput, label="Password")
#
#     def __init__(self, request, *args, **kwargs):
#         super().__init__(*args, **kwargs)
