from django.urls import path, include
from . import views

app_name = 'chats'

urlpatterns = [
    path('my-chatbots/', views.ListChats.as_view(), name='list_chats'),
    path('initiate-chatbot-creation/', views.initiate_chatbot_creation,
         name='initiate_chatbot_creation'),
    path('<uuid:chat_uuid>/add-files/', views.AddFilesListView.as_view(),
         name='add_files'),
    path('<uuid:chat_uuid>/submit-files/', views.FilesSubmitView.as_view(),
         name='submit_files'),
    path('<uuid:chat_uuid>/delete-file/<int:file_id>', views.chat_file_delete,
         name='delete-file'),

    path('<uuid:chat_uuid>/add-text/', views.AddTextView.as_view(),
         name='add_text'),
]
