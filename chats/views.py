from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import View, ListView, TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SmartChat, ChatFile, ChatText
from . import forms
from django.contrib import messages
from django.http import HttpResponse, FileResponse


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


@login_required()
def initiate_chatbot_creation(request):
    user = request.user
    chatbots_available = (user.chatbots_available
                          - user.chatbots.filter(active=True).count())
    if chatbots_available <= 0:
        messages.error(request, "Достигнут лимит количества чат-ботов")
        return redirect('chats:list_chats')
    new_chat = SmartChat(owner=user)
    new_chat.save()
    return redirect('chats:add_files', chat_uuid=new_chat.pk)


class AddFilesListView(LoginRequiredMixin, ListView):
    model = ChatFile
    template_name = 'chats/general/chat_add_files.html'
    context_object_name = 'chat_files'
    # paginate_by

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.smartchat = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        chat_uuid = self.kwargs.get('chat_uuid')
        self.smartchat = get_object_or_404(SmartChat, id=chat_uuid,
                                           owner=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.smartchat.files.all().order_by('-created')
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['smartchat_characters'] = self.smartchat.character_length
        context['chat_uuid'] = self.smartchat.id
        context['chat_character_limit'] = (
            self.smartchat.owner.chatbot_character_limit
        )
        return context


class FilesSubmitView(LoginRequiredMixin, View):
    ALLOWED_EXTENSIONS = ['txt', 'doc', 'docx', 'pdf', 'html']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat = None
        self.chat_character_limit = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        chat_uuid = self.kwargs.get('chat_uuid')
        self.chat = get_object_or_404(SmartChat, id=chat_uuid,
                                      owner=self.request.user)
        self.chat_character_limit = self.chat.owner.chatbot_character_limit
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, chat_uuid):
        for submitted_file in request.FILES.getlist('file'):
            file_length_in_bytes = 0
            if submitted_file.name.split('.')[-1].lower() not in self.ALLOWED_EXTENSIONS:
                messages.error(
                    request,
                    f"Расширение файла {submitted_file.name} не поддерживается"
                )
                continue
            for chunk in submitted_file.chunks():
                file_length_in_bytes += len(chunk)
            chat_file = ChatFile(file=submitted_file, chat=self.chat,
                                 character_length=file_length_in_bytes)
            self.chat.character_length += file_length_in_bytes
            if (self.chat.character_length
                    <= self.chat_character_limit):
                chat_file.save()
            else:
                self.chat.character_length -= file_length_in_bytes
                messages.error(
                    request,
                    f"Размер файла {submitted_file.name} "
                    f"{file_length_in_bytes} символов превышает допустимый лимит"
                )
        self.chat.save()
        return redirect(reverse('chats:add_files', kwargs={'chat_uuid': chat_uuid}))


@login_required()
def chat_file_delete(request, chat_uuid, file_id):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    file = get_object_or_404(ChatFile, chat=chat, pk=file_id)
    chat.character_length -= file.character_length
    file.delete()
    chat.save()
    return redirect(reverse('chats:add_files', kwargs={'chat_uuid': chat_uuid}))


class AddTextView(LoginRequiredMixin, FormView):
    template_name = 'chats/general/chat_add_text.html'
    form_class = forms.AddTextFrom

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.smartchat = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        chat_uuid = self.kwargs.get('chat_uuid')
        self.smartchat = get_object_or_404(SmartChat, id=chat_uuid,
                                           owner=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['smartchat_characters'] = self.smartchat.character_length
        context['chat_uuid'] = self.smartchat.id
        context['chat_character_limit'] = (
            self.smartchat.owner.chatbot_character_limit
        )
        return context

    def get_initial(self):
        initial = super().get_initial()
        chat_texts = ChatText.objects.filter(is_question=False)
        if chat_texts:
            initial['chat_text'] = chat_texts[0].answer
        return initial

    def form_valid(self, form):
        submitted_text = form.cleaned_data['chat_text']
        chat_text, created = ChatText.objects.get_or_create(
            chat=self.smartchat, is_question=False
        )
        initial_length = 0
        if not created:
            initial_length = len(chat_text.answer)
        chat_text.answer = submitted_text
        chat_text.save()
        self.smartchat.character_length += len(submitted_text) - initial_length
        self.smartchat.save()
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        messages.error("Что-то пошло не так")
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))
