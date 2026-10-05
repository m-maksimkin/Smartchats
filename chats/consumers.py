import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .llm_utils.chat_context import build_chat_engine, ensure_chat_index
from .models import SmartChat

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_engine = None

    async def connect(self):
        await self.accept()
        user = self.scope.get('user')
        chat_uuid = self.scope['url_route']['kwargs']['chat_uuid']
        if user is None or not user.is_authenticated:
            await self.close()
            return
        owns_chat = await SmartChat.objects.filter(id=chat_uuid, owner_id=user.id).aexists()
        if not owns_chat:
            await self.close()
            return

        await self.send(text_data=json.dumps({'status': 'indexing'}))
        try:
            await ensure_chat_index(chat_uuid)
            self.chat_engine = build_chat_engine(chat_uuid)
        except Exception:
            logger.exception('Failed to prepare chat %s', chat_uuid)
            await self.send(text_data=json.dumps({'status': 'error'}))
            await self.close()
            return
        await self.send(text_data=json.dumps({'status': 'ready'}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        if self.chat_engine:
            response = await self.chat_engine.achat(message)
            await self.send(text_data=json.dumps({'message': response.response}))
