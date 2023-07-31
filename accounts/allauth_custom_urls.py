from django.urls import path, include
from allauth.urls import urlpatterns as allauth_urlpatterns
from .views import signup_redirect_view, account_inactive_view

urlpatterns = [
    path('social/signup/', signup_redirect_view, name='signup_redirect'),
    path('inactive/', account_inactive_view, name='account_inactive'),
]

urlpatterns += allauth_urlpatterns[1:]
