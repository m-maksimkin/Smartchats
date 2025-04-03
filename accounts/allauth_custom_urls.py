from allauth.urls import urlpatterns as allauth_urlpatterns
from django.urls import include, path

from .views import account_inactive_view, signup_redirect_view

urlpatterns = [
    path('social/signup/', signup_redirect_view, name='signup_redirect'),
    path('inactive/', account_inactive_view, name='account_inactive'),
]

urlpatterns += allauth_urlpatterns[1:]
