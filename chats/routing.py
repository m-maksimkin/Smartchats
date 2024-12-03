from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
 re_path(r'ws/chats/(?P<chat_uuid>[a-f0-9\-]{36})/$',
         consumers.ChatConsumer.as_asgi()),
]
