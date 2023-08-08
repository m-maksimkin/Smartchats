from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('sign-up/', views.sign_up_view, name='sign_up'),
    path('email-verify/<uidb64>/<token>/', views.email_verify_view, name='email_verify'),
    path('initiate-password-reset/', views.initiate_password_reset_view, name='initiate_password_reset'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_view, name='password_reset'),
    path('', views.account_index, name='account_index'),
]
