from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from chats.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('chats/', include('chats.urls', namespace='chats')),
    path('oauth/', include('accounts.allauth_custom_urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
