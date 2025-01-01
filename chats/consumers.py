import json

from asgiref.sync import sync_to_async
from django.core.cache import cache
from channels.generic.websocket import AsyncWebsocketConsumer

from .llm_utils.chat_context import IndexManager


class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_engine = None

    async def connect(self):
        await self.accept()
        index = await IndexManager.get_load_or_create_index(
            self.scope['url_route']['kwargs']['chat_uuid'],
            self.scope["session"].session_key
        )
        self.query_engine = index.as_query_engine(similarity_top_k=2, similarity_threshold=0.1)

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        if self.query_engine:
            response = await self.query_engine.aquery(message)
            await self.send(text_data=json.dumps({'message': response.response}))
