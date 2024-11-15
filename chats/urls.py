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
    path('<uuid:chat_uuid>/delete-file/<int:file_id>/', views.chat_file_delete,
         name='delete-file'),

    path('<uuid:chat_uuid>/add-text/', views.AddTextView.as_view(),
         name='add_text'),

    path('<uuid:chat_uuid>/add-questions/', views.AddQuestionListView.as_view(),
         name='add_questions'),
    path('<uuid:chat_uuid>/create-question/', views.update_chat_question,
         name='create_question'),
    path('<uuid:chat_uuid>/update-question/<int:question_id>/',
         views.update_chat_question, name='update_question'),
    path('<uuid:chat_uuid>/delete-question/<int:question_id>/',
         views.chat_question_delete, name='delete_question'),

    path('<uuid:chat_uuid>/add-url/', views.ChatAddURL.as_view(),
         name='add_url'),
    path('<uuid:chat_uuid>/delete-url/<int:url_id>/', views.chat_url_delete,
         name='delete_url'),
    path('<uuid:chat_uuid>/delete-all-urls/', views.chat_url_delete,
         name='delete_all_urls'),

    path('<uuid:chat_uuid>/create-chatbot/', views.initiate_chat_creation, name='create_chatbot'),
    path('<uuid:chat_uuid>/playground/', views.ChatPlayground.as_view(), name='chat_playground'),
]
