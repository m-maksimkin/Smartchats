import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .llm_utils.chat_context import build_chat_engine, ensure_chat_index
from .models import SmartChat
from .services.chat_settings import aget_chat_settings

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000


class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_uuid = None
        self.chat_engine = None

    async def connect(self):
        await self.accept()
        user = self.scope.get('user')
        self.chat_uuid = self.scope['url_route']['kwargs']['chat_uuid']
        if user is None or not user.is_authenticated:
            await self.close()
            return
        owns_chat = await SmartChat.objects.filter(id=self.chat_uuid, owner_id=user.id).aexists()
        if not owns_chat:
            await self.close()
            return
        await self._prepare_engine()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or '')
        except json.JSONDecodeError:
            return
        if payload.get('type') == 'reset':
            await self._prepare_engine()
        elif payload.get('type') == 'message':
            await self._answer(str(payload.get('text', '')).strip()[:MAX_MESSAGE_LENGTH])

    async def _prepare_engine(self):
        self.chat_engine = None
        await self._send_json({'type': 'status', 'state': 'indexing'})
        try:
            await ensure_chat_index(self.chat_uuid)
            chat_settings = await aget_chat_settings(self.chat_uuid)
            self.chat_engine = build_chat_engine(chat_settings)
        except Exception:
            logger.exception('Failed to prepare chat %s', self.chat_uuid)
            await self._send_json({'type': 'status', 'state': 'error'})
            return
        await self._send_json({'type': 'status', 'state': 'ready'})

    async def _answer(self, text):
        if not text or self.chat_engine is None:
            return
        try:
            response = await self.chat_engine.astream_chat(text)
            async for delta in response.async_response_gen():
                await self._send_json({'type': 'delta', 'text': delta})
        except Exception:
            logger.exception('Chat %s failed to answer', self.chat_uuid)
            await self._send_json({'type': 'error', 'message': 'Не удалось получить ответ'})
            return
        await self._send_json({'type': 'done', 'sources': _source_labels(response.source_nodes)})

    async def _send_json(self, payload):
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))


def _source_labels(source_nodes):
    labels = []
    for node_with_score in source_nodes:
        label = node_with_score.node.metadata.get('source')
        if label and label not in labels:
            labels.append(label)
    return labels
