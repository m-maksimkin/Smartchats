import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from chats.llm_utils.vector_store import delete_chat_vectors
from chats.models import SmartChat


class Command(BaseCommand):
    help = 'Deletes all chats.'

    def handle(self, *args, **options):
        smartchats = SmartChat.objects.all()
        for smartchat in smartchats:
            chat_id = str(smartchat.id)
            path_to_smartchat_files = os.path.join(settings.MEDIA_ROOT, chat_id)
            smartchat.delete()
            delete_chat_vectors(chat_id)
            if os.path.exists(path_to_smartchat_files):
                shutil.rmtree(path_to_smartchat_files)
