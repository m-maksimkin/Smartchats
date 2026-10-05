import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

from .llm_utils.chat_context import IndexManager
from .llm_utils.llm_factory import get_llm
from .llm_utils.prompts import get_chat_prompt_templates


class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_engine = None

    async def connect(self):
        await self.accept()
        chat_uuid = self.scope['url_route']['kwargs']['chat_uuid']
        index = await IndexManager.get_load_or_create_index(chat_uuid)
        prompts = get_chat_prompt_templates(chat_uuid)
        retriever = index.as_retriever(similarity_top_k=settings.RAG_SIMILARITY_TOP_K)
        self.chat_engine = ContextChatEngine.from_defaults(
            retriever=retriever,
            llm=get_llm(),
            system_prompt=prompts['system_prompt'],
            context_template=prompts['context_template'],
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=settings.RAG_SIMILARITY_THRESHOLD),
            ],
        )

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        if self.chat_engine:
            response = await self.chat_engine.achat(message)
            await self.send(text_data=json.dumps({'message': response.response}))
