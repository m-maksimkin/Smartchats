from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import connection
from django.db.models import Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView, TemplateView, View

from . import forms
from .models import ChatFile, ChatText, ChatURL, SmartChat
from .tasks import crawl_url_task

ALLOWED_EXTENSIONS = ['txt', 'doc', 'docx', 'pdf', 'html']


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
            self.request.user.chatbot_character_limit
        )
        context['smartchat_active'] = self.smartchat.active
        return context


class FilesSubmitView(LoginRequiredMixin, View):

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
        self.chat_character_limit = self.request.user.chatbot_character_limit
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, chat_uuid):
        saved_files = []
        for submitted_file in request.FILES.getlist('file'):
            file_length_in_bytes = 0
            if submitted_file.name.split('.')[-1].lower() not in ALLOWED_EXTENSIONS:
                messages.error(
                    request,
                    f"Расширение файла {submitted_file.name} не поддерживается"
                )
                continue
            for chunk in submitted_file.chunks():
                file_length_in_bytes += len(chunk)
            character_approximation = file_length_in_bytes // 2
            chat_file = ChatFile(file=submitted_file, chat=self.chat,
                                 character_length=character_approximation)
            self.chat.character_length += character_approximation
            if (self.chat.character_length
                    <= self.chat_character_limit):
                chat_file.save()
                saved_files.append(chat_file)
            else:
                self.chat.character_length -= character_approximation
                messages.error(
                    request,
                    f"Размер файла {submitted_file.name} "
                    f"{file_length_in_bytes} символов превысил допустимый лимит для чатбота"
                )
        self.chat.save()
        return render(
            request, 'chats/general/partials/submit_files.html',
            {'saved_files': saved_files, 'smartchat_characters': self.chat.character_length, 'chat_uuid': chat_uuid}
        )


@login_required
@require_POST
def chat_file_delete(request, chat_uuid, file_id):
    file = get_object_or_404(
        ChatFile.objects.select_related('chat'),
        chat__id=chat_uuid,
        chat__owner=request.user,
        pk=file_id
    )
    file.chat.character_length -= file.character_length
    file.delete()
    file.chat.save()
    return render(
        request, 'chats/general/partials/delete_source.html',
        {'smartchat_characters': file.chat.character_length}
    )


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
def create_chat_question(request, chat_uuid):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    question = ChatText(chat=chat)
    initial_len = 0
    form = forms.ChatAddQuestionForm(request.POST, instance=question)
    if form.is_valid():
        cl = form.cleaned_data
        form.save()
        chat.character_length += (len(cl.get('question')) + len(cl.get('answer'))
                                  - initial_len)
        chat.save()
        create_form = forms.ChatAddQuestionForm()
        return render(
            request, 'chats/general/partials/create_question.html',
            {'form': form, 'create_form': create_form,
             'chat_uuid': chat_uuid, 'smartchat_characters': question.chat.character_length}
        )
    else:
        messages.error(request, "Что-то пошло не так")
        return render(
            request, 'chats/general/partials/create_question.html',
            {'chat_uuid': chat_uuid, 'smartchat_characters': question.chat.character_length}
        )


@login_required
@require_POST
def update_chat_question(request, chat_uuid, question_id):
    if question_id:
        question = get_object_or_404(
            ChatText.objects.select_related('chat'),
            chat__id=chat_uuid,
            chat__owner=request.user,
            pk=question_id
        )
    form = forms.ChatAddQuestionForm(request.POST, instance=question)
    initial_len = len(question.question) + len(question.answer)
    if form.is_valid():
        cl = form.cleaned_data
        question.chat.character_length += len(cl.get('question')) + len(cl.get('answer')) - initial_len
        form.save()
        question.chat.save()
    else:
        messages.error(request, 'Что-то пошло не так')
    return render(
        request, 'chats/general/partials/update_question.html',
        {'form': form, 'chat_uuid': chat_uuid, 'smartchat_characters': question.chat.character_length}
    )


@login_required
@require_POST
def chat_question_delete(request, chat_uuid, question_id):
    question = get_object_or_404(
        ChatText.objects.select_related('chat'),
        chat__id=chat_uuid,
        chat__owner=request.user,
        pk=question_id
    )
    question_len = len(question.question) + len(question.answer)
    question.chat.character_length -= question_len
    question.delete()
    question.chat.save()
    return render(
        request, 'chats/general/partials/delete_source.html',
        {'smartchat_characters': question.chat.character_length}
    )


class ChatAddURL(LoginRequiredMixin, TemplateView):
    template_name = 'chats/general/chat_add_url.html'

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
        context['form'] = forms.ChatCrawlUrlForm()
        context['smartchat_characters'] = self.smartchat.character_length
        context['chat_uuid'] = self.smartchat.id
        context['chat_character_limit'] = (
            self.smartchat.owner.chatbot_character_limit
        )
        context['smartchat_active'] = self.smartchat.active
        context['chat_urls'] = self.smartchat.urls.all().order_by('created')
        redis_key = f"crawler_task:{self.smartchat.id}"
        context['crawling_task_active'] = bool(cache.get(redis_key))
        return context


@login_required
@require_POST
def start_crawler(request, chat_uuid):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    form = forms.ChatCrawlUrlForm(request.POST)
    hx_trigger = 'false'
    if form.is_valid():
        start_url = form.cleaned_data['crawl_url']
        redis_key = f"crawler_task:{chat_uuid}"
        if cache.get(redis_key):
            messages.error(request, 'Дождитесь завершения запущенной обработки')
        else:
            task = crawl_url_task.delay(start_url, chat_uuid)
            cache.set(redis_key, task.id, timeout=600)
            hx_trigger = 'true'
    else:
        messages.error(request, 'Введите корректный url')
    response = render(request, 'partial_messages.html')
    response['HX-Trigger'] = hx_trigger
    return response


class ListChatUrls(LoginRequiredMixin, ListView):
    model = ChatURL
    template_name = 'chats/general/partials/list_chat_urls.html'
    context_object_name = 'chat_urls'

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
        return self.smartchat.urls.all().order_by('created')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['smartchat_characters'] = self.smartchat.character_length
        context['chat_uuid'] = self.smartchat.id
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        redis_key = f"crawler_task:{self.smartchat.id}"
        hx_trigger = 'false' if cache.get(redis_key) else 'true'
        response['HX-Trigger'] = hx_trigger
        return response


@login_required
@require_POST
def chat_url_delete(request, chat_uuid, url_id=None):
    chat = get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)
    if url_id is None:
        all_urls = chat.urls.all()
        if all_urls:
            total_length = all_urls.aggregate(total_length=Sum('character_length'))['total_length']
            chat.character_length -= total_length
            all_urls.delete()
            chat.save()
        return redirect(reverse('chats:add_url', kwargs={'chat_uuid': chat_uuid}))
    chat_url = get_object_or_404(ChatURL, chat=chat, pk=url_id)
    chat.character_length -= chat_url.character_length
    chat_url.delete()
    chat.save()
    return render(
        request, 'chats/general/partials/delete_source.html',
        {'smartchat_characters': chat.character_length}
    )


@login_required
@require_POST
def initiate_chat_creation(request, chat_uuid):
    chat = get_object_or_404(SmartChat.objects.select_related('owner'), id=chat_uuid, owner=request.user)
    referer_url = request.META.get('HTTP_REFERER', reverse('chats:add_files', kwargs={'chat_uuid': chat_uuid}))
    if cache.get(f"crawler_task:{chat_uuid}"):
        messages.error(request, 'Дождитесь завершения сбора данных по url')
        return redirect(referer_url)

    remaining_chars = chat.owner.chatbot_character_limit - chat.character_length
    if remaining_chars < 0:
        messages.error(request, 'Превышен лимит доступных символов для чатбота')
        return redirect(referer_url)

    chat.active = True
    chat.save()
    messages.warning(request, 'Обучение чатбота запущено')
    # clear index in cache
    return redirect('chats:chat_playground', chat_uuid)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chat_uuid'] = self.smartchat.id
        return context
