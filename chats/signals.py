from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ChatFile, ChatIndex, ChatText, ChatURL, SmartChat


@receiver(post_save, sender=ChatText)
@receiver(post_save, sender=ChatFile)
@receiver(post_save, sender=ChatURL)
def index_need_update_on_datasource_save(sender, instance, created, **kwargs):
    smartchat = instance.chat
    if smartchat:
        try:
            chat_index = ChatIndex.objects.get(chat=smartchat)
            chat_index.need_update = True
            chat_index.save()
        except ChatIndex.DoesNotExist:
            pass


@receiver(post_save, sender=ChatText)
@receiver(post_save, sender=ChatFile)
@receiver(post_save, sender=ChatURL)
def index_need_update_on_datasource_delete(sender, instance, **kwargs):
    smartchat = instance.chat
    if smartchat:
        try:
            chat_index = ChatIndex.objects.get(chat=smartchat)
            chat_index.need_update = True
            chat_index.save()
        except ChatIndex.DoesNotExist:
            pass
