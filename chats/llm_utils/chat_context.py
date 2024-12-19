import os.path
import asyncio

from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.conf import settings

from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import StorageContext

from ..models import SmartChat, ChatIndex, ChatText, ChatURL, ChatFile


# async def get_documents_for_chat(chat_uuid):
#     texts = ChatText.objects.filter(chat=chat_uuid)
#     documents = []
#     async for text in texts:
#         for char in text.answer:
#             print(char)
#         documents.append(Document(text=text.question + '\n' + text.answer, id_=f'text_{str(text.id)}'))
#
#     chat_files_dir = os.path.join(settings.MEDIA_ROOT, chat_uuid, 'source_files')
#     if os.path.exists(chat_files_dir):
#         documents.extend(SimpleDirectoryReader(input_dir=chat_files_dir).load_data())
#
#
#     print((documents))
#     # IngestionPipeline(transformations=transformations)
#     # nodes = await pipline.arun(documents=documents)
#
#
# async def get_load_or_create_index(chat_uuid, session_key):
#     index_key = f'index:{chat_uuid}'
#     index = await sync_to_async(cache.get)(index_key)
#     if index is not None:
#         return index
#
#     try:
#         chat_index = await sync_to_async(ChatIndex.objects.get)(chat_id=chat_uuid)
#     except ChatIndex.DoesNotExist:
#         chat_index = None
#     if chat_index and chat_index.index_dir:
#         if not chat_index.need_update:
#             # handle load from directory ,return index
#             ...
#         else:
#             # do refresh return index
#             ...
#     await get_documents_for_chat(chat_uuid)


class IndexManager:
    _indexes: dict[str, VectorStoreIndex] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_load_or_create_index(cls, chat_uuid, session_key):
        index = cls._indexes.get(chat_uuid)
        if index is not None:
            return index

        async with cls._lock:
            try:
                chat_index = await sync_to_async(ChatIndex.objects.get)(chat_id=chat_uuid)
            except ChatIndex.DoesNotExist:
                chat_index = None
            if chat_index and chat_index.index_dir:
                if not chat_index.need_update:
                    # handle load from directory ,return index
                    ...
                else:
                    # do refresh return index
                    ...

            documents = await cls.get_documents_for_chat(chat_uuid)
            print(documents)

    @classmethod
    async def get_documents_for_chat(cls, chat_uuid):
        documents = []
        texts = ChatText.objects.filter(chat=chat_uuid)
        async for text in texts:
            documents.append(Document(text=text.question + '\n' + text.answer, id_=f'text_{str(text.id)}'))

        chat_files_paths = []
        async for chat_file in ChatFile.objects.filter(chat=chat_uuid):
            chat_files_paths.append(chat_file.file.path)
        if chat_files_paths:
            file_documents = await cls._load_files_sync(chat_files_paths)
            documents.extend(file_documents)

        chat_urls = ChatURL.objects.filter(chat=chat_uuid)
        async for chat_url in chat_urls:
            documents.append(Document(text=chat_url.url_text, id_=f'url_{str(chat_url.id)}'))
        return documents

    @classmethod
    @sync_to_async
    def _load_files_sync(cls, filepaths):
        return SimpleDirectoryReader(input_files=filepaths, filename_as_id=True).load_data()
