import json
from django.core.cache import cache
from channels.generic.websocket import AsyncWebsocketConsumer

from .llm_utils.chat_context import IndexManager


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.kwargs.chat_uuid
        # scope["session"].session_key
        await IndexManager.get_load_or_create_index(self.scope['url_route']['kwargs']['chat_uuid'], self.scope["session"].session_key)
        # cache.set('sas', AsyncWebsocketConsumer, 50)
        # print(cache.get('sas'))
        await self.accept()

    async def disconnect(self, close_code):
        #
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.send(text_data=json.dumps({'message': message}))
