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
        validators=[FileExtensionValidator(['txt', 'docx', 'pdf', 'html'])]
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


class ChatIndex(models.Model):
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE,
                             related_name="index")
    need_update = models.BooleanField(default=False)
    index_dir = models.CharField(max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
