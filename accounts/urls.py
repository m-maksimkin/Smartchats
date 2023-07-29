from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('sign-up/', views.sign_up_view, name='sign_up'),
    path('email-verify/<uidb64>/<token>/', views.email_verify_view, name='email_verify'),
    # path('', include('django.contrib.auth.urls')),
    path('', views.account_index, name='account_index'),
]