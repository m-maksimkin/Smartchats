import os
import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class SmartChat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="chatbots")
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=50, default="Chat")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    character_length = models.IntegerField(default=0)


def get_upload_path(instance, filename):
    chat_id = instance.chat.id
    if isinstance(instance, ChatURL):
        return f"{chat_id}/source_files/crawl_response/{filename}"
    else:
        return f"{chat_id}/source_files/{filename}"


class ChatFile(models.Model):
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(settings.ALLOWED_UPLOAD_EXTENSIONS)]
    )
    file_name = models.CharField(max_length=256, blank=True)
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE, related_name="files")
    character_length = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.file_name:
            self.file_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


class ChatText(models.Model):
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE,
                             related_name="texts")
    is_question = models.BooleanField(default=True, db_index=True)
    question = models.CharField(max_length=1000, blank=True,
                                default='', db_index=True)
    answer = models.TextField(max_length=10**5)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ChatURL(models.Model):
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE,
                             related_name="urls")
    url = models.URLField()
    # url_html_response = models.FileField(
    #     upload_to=get_upload_path,
    #     validators=[FileExtensionValidator(['html'])]
    # )
    url_text = models.TextField(max_length=500000)
    character_length = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


def default_chat_model():
    return settings.OPENAI_MODEL


def default_similarity_top_k():
    return settings.RAG_SIMILARITY_TOP_K


def default_similarity_cutoff():
    return settings.RAG_SIMILARITY_THRESHOLD


def default_instructions():
    from .llm_utils.prompts import DEFAULT_INSTRUCTIONS
    return DEFAULT_INSTRUCTIONS


class ChatSettings(models.Model):
    class ReasoningEffort(models.TextChoices):
        NONE = 'none', 'Без рассуждений'
        LOW = 'low', 'Низкая'
        MEDIUM = 'medium', 'Средняя'
        HIGH = 'high', 'Высокая'

    chat = models.OneToOneField(SmartChat, on_delete=models.CASCADE,
                                related_name='chat_settings')
    instructions = models.TextField(max_length=10000, default=default_instructions)
    model = models.CharField(max_length=64, default=default_chat_model)
    temperature = models.FloatField(default=0.2)
    reasoning_effort = models.CharField(max_length=16, choices=ReasoningEffort.choices,
                                        default=ReasoningEffort.LOW)
    max_output_tokens = models.PositiveIntegerField(null=True, blank=True)
    similarity_top_k = models.PositiveSmallIntegerField(default=default_similarity_top_k)
    similarity_cutoff = models.FloatField(default=default_similarity_cutoff)
    rewrite_followups = models.BooleanField(default=True)

    display_name = models.CharField(max_length=60, blank=True, default='')
    welcome_message = models.CharField(max_length=500, blank=True,
                                       default='Здравствуйте! Чем могу помочь?')
    suggested_messages = models.JSONField(default=list, blank=True)
    input_placeholder = models.CharField(max_length=120, blank=True,
                                         default='Напишите сообщение...')
    accent_color = models.CharField(max_length=7, default='#17202b')

    updated = models.DateTimeField(auto_now=True)


class ChatIndex(models.Model):
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE,
                             related_name="index")
    need_update = models.BooleanField(default=False)
    index_dir = models.CharField(max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
