from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email", max_length=100, validators=[EmailValidator],
        widget=forms.EmailInput(attrs={"placeholder": _("Введите email")})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs["placeholder"] = _("Введите пароль")
        self.error_messages["invalid_login"] = (
            _("Пожалуйста ведите правильный адрес почты и пароль.")
        )


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=100, validators=[EmailValidator],
        widget=forms.EmailInput(attrs={"placeholder": _("Введите email")})
    )
    password1 = forms.CharField(
        label=_("Пароль"), max_length=50,
        widget=forms.PasswordInput(attrs={"placeholder": _("Введите пароль")})
    )
    password2 = forms.CharField(
        label=_("Пароль"), max_length=50,
        widget=forms.PasswordInput(attrs={"placeholder": _("Повторите пароль")})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email.lower()
        raise forms.ValidationError(_("Аккаунт с таким email уже существует"))

    def clean_password2(self):
        password2 = self.cleaned_data['password2']
        validate_password(password2)
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', _("Пароли не совпадают"))
        return cleaned_data

    def create_user(self):
        cl = self.cleaned_data
        user = User(email=cl['email'], is_active=False)
        user.set_password(cl['password1'])
        user.save()
        return user


class InitiatePasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=100, validators=[EmailValidator],
        widget=forms.EmailInput(attrs={"placeholder": _("Введите email")})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError(_("Аккаунт с таким email не существует"))
        social_accounts = user.socialaccount_set.all()
        if social_accounts:
            raise forms.ValidationError(_("Ваш аккаунт зарегистрирован с помощью социальных сетей. "
                                          f"Выполните вход через {social_accounts[0].provider}"))
        return email.lower()

    def get_user(self):
        email = self.cleaned_data['email']
        user = User.objects.get(email=email)
        return user


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label=_("Пароль"), max_length=50,
        widget=forms.PasswordInput(attrs={"placeholder": _("Введите новый пароль")})
    )
    password2 = forms.CharField(
        label=_("Пароль"), max_length=50,
        widget=forms.PasswordInput(attrs={"placeholder": _("Повторите пароль")})
    )

    def clean_password2(self):
        password2 = self.cleaned_data['password2']
        validate_password(password2)
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', _("Пароли не совпадают"))
        return cleaned_data
