from django.urls import path, include
from . import views

app_name = 'chats'

urlpatterns = [
    path('my-chatbots/', views.ListChats.as_view(), name='list_chats'),
    path('initiate-chatbot-creation', views.initiate_chatbot_creation,
         name='initiate_chatbot_creation'),

    path('add-file/', views.chat_add_file),
]
