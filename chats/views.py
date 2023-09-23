from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SmartChat
from . import forms
from django.contrib import messages
from django.http import HttpResponse


class ListChats(LoginRequiredMixin, ListView):
    template_name = 'chats/general/chats_list.html'
    context_object_name = 'chats_list'

    def get_queryset(self):
        return SmartChat.objects.filter(owner=self.request.user, active=True)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        chatbots_left = (user.chatbots_available
                         - user.chatbots.filter(active=True).count())
        context['chatbots_left'] = chatbots_left
        return context


def initiate_chatbot_creation(request):
    user = request.user
    chatbots_available = (user.chatbots_available
                          - user.chatbots.filter(active=True).count())
    if chatbots_available <= 0:
        messages.error(request, "Достигнут лимит количества чат-ботов")
        return redirect('chats:list_chats')
    new_chat = SmartChat(owner=user)
    new_chat.save()
    return HttpResponse(new_chat.pk)


def chat_add_file(request):
    form = forms.AddFileForm()
    return render(request, 'chats/general/chat_add_file.html',
                  {'form': form})
