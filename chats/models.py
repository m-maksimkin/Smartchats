import uuid
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


def get_upload_path(instance, filename):
    chat_id = instance.chat.id
    return f"{chat_id}/source_files/{filename}"


class ChatFile(models.Model):
    file = models.FileField(upload_to=get_upload_path,
                            validators=[FileExtensionValidator(['txt', 'docx', 'pdf', 'html'])])
    chat = models.ForeignKey(SmartChat, on_delete=models.CASCADE, related_name="files")

