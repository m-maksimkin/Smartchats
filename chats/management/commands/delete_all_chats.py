from django.core.management.base import BaseCommand
from django.conf import settings

import os
import shutil

from chats.models import SmartChat


class Command(BaseCommand):
    help = 'Deletes all chats.'

    def handle(self, *args, **options):
        smartchats = SmartChat.objects.all()
        for smartchat in smartchats:
            path_to_smartchat_files = os.path.join(settings.MEDIA_ROOT, str(smartchat.id))
            smartchat.delete()
            if os.path.exists(path_to_smartchat_files):
                shutil.rmtree(path_to_smartchat_files)
