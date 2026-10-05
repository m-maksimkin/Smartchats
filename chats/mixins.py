from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from .models import SmartChat


class SmartChatOwnerMixin(LoginRequiredMixin):
    smartchat = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        chat_uuid = self.kwargs.get('chat_uuid')
        self.smartchat = get_object_or_404(
            SmartChat, id=chat_uuid, owner=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def smartchat_context(self):
        return {
            'smartchat_characters': self.smartchat.character_length,
            'chat_uuid': self.smartchat.id,
            'chat_character_limit': self.request.user.chatbot_character_limit,
            'smartchat_active': self.smartchat.active,
        }
