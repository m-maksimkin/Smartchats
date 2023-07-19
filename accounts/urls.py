from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("sign-up/", views.sign_up_view, name="sign_up"),
    # path('', include('django.contrib.auth.urls')),
    path('', views.account_index, name="account_index"),
]