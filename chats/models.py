import uuid
import os
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator


class SmartChat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="chatbots")
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=50, default="Chat")
    created = models.DateTimeField(auto_now_add=True)
    character_length = models.IntegerField(default=0)


def get_upload_path(instance, filename):
    chat_id = instance.chat.id
    return f"{chat_id}/source_files/{filename}"


class ChatFile(models.Model):
    file = models.FileField(upload_to=get_upload_path,
                            validators=[FileExtensionValidator(['txt', 'docx', 'pdf', 'html'])])
    file_name = models.CharField(max_length=256, blank=True)
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE, related_name="files")
    character_length = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.file_name:
            self.file_name = os.path.basename(self.file.name)
            super().save(*args, **kwargs)
