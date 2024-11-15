from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import View, ListView, TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SmartChat, ChatFile, ChatText, ChatURL
from django.db import connection
from django.db.models import Sum
from . import forms
from .utils import crawl_url
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
        context['smartchat_active'] = self.smartchat.active
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


@login_required
@require_POST
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
        context['smartchat_active'] = self.smartchat.active
        return context

    def get_initial(self):
        initial = super().get_initial()
        chat_texts = ChatText.objects.filter(chat=self.smartchat, is_question=False)
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
        messages.error(self.request, "Что-то пошло не так")
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))


class AddQuestionListView(LoginRequiredMixin, TemplateView):
    template_name = 'chats/general/chat_add_questions.html'

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
        context['smartchat_active'] = self.smartchat.active
        questions_queryset = (
            self.smartchat.texts.filter(is_question=True).order_by('created')
        )
        form_list = []
        for question in questions_queryset:
            form_list.append(forms.ChatAddQuestionForm(instance=question))
        context['form_list'] = form_list
        context['create_form'] = forms.ChatAddQuestionForm()
        return context


@login_required
@require_POST
def update_chat_question(request, chat_uuid, question_id=None):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    if question_id:
        question = get_object_or_404(ChatText, chat=chat, pk=question_id)
        initial_len = len(question.question) + len(question.answer)
    else:
        question = ChatText(chat=chat)
        initial_len = 0
    form = forms.ChatAddQuestionForm(request.POST, instance=question)
    if form.is_valid():
        cl = form.cleaned_data
        form.save()
        chat.character_length += (len(cl.get('question')) + len(cl.get('answer'))
                                  - initial_len)
        chat.save()
        return redirect(reverse('chats:add_questions', args=[chat_uuid]))
    else:
        messages.error(request, "Что-то пошло не так")
        return redirect(reverse('chats:add_questions', args=[chat_uuid]))


@login_required
@require_POST
def chat_question_delete(request, chat_uuid, question_id):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    question = get_object_or_404(ChatText, chat=chat, pk=question_id)
    question_len = len(question.question) + len(question.answer)
    chat.character_length -= question_len
    question.delete()
    chat.save()
    return redirect(reverse('chats:add_questions', kwargs={'chat_uuid': chat_uuid}))


class ChatAddURL(LoginRequiredMixin, FormView):
    template_name = 'chats/general/chat_add_url.html'
    form_class = forms.ChatCrawlUrlForm

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
        context['smartchat_active'] = self.smartchat.active
        context['chat_urls'] = self.smartchat.urls.all().order_by('created')
        return context

    def form_valid(self, form):
        url = form.cleaned_data['crawl_url']
        crawl_url(url, self.smartchat, self.request)
        return self.render_to_response(self.get_context_data(form=form))


@login_required
@require_POST
def chat_url_delete(request, chat_uuid, url_id=None):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    if url_id is None:
        all_urls = chat.urls.all()
        total_length = all_urls.aggregate(total_length=Sum('character_length'))['total_length']
        chat.character_length -= total_length
        all_urls.delete()
        chat.save()
        return redirect(reverse('chats:add_url', kwargs={'chat_uuid': chat_uuid}))
    chat_url = get_object_or_404(ChatURL, chat=chat, pk=url_id)
    chat.character_length -= chat_url.character_length
    chat_url.delete()
    chat.save()
    return redirect(reverse('chats:add_url', kwargs={'chat_uuid': chat_uuid}))


@login_required
@require_POST
def initiate_chat_creation(request, chat_uuid):
    chat = get_object_or_404(SmartChat.objects.select_related('owner'), id=chat_uuid, owner=request.user)
    chars = chat.owner.chatbot_character_limit - chat.character_length
    if chars >= 0:
        chat.active = True
        chat.save()
        messages.warning(request, 'Обучение чатбота запущено')
        # clear index in cache
        return redirect('chats:chat_playground', chat_uuid)
    messages.error(request, 'Превышен лимит доступных символов для чатбота')
    referer_url = request.META.get('HTTP_REFERER', reverse('chats:add_files', kwargs={'chat_uuid': chat_uuid}))
    return redirect(referer_url)


class ChatPlayground(LoginRequiredMixin, TemplateView):
    template_name = 'chats/created_chats/playground.html'

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
