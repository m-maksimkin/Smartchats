import os.path
import asyncio

from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.conf import settings

from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader,\
    StorageContext, load_index_from_storage
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.simple import SimpleVectorStore
from llama_index.llms.openai import OpenAI

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from ..models import SmartChat, ChatIndex, ChatText, ChatURL, ChatFile


Settings.llm = OpenAI(model="gpt-4o-mini-2024-07-18")

class IndexManager:
    _indexes: dict[str, VectorStoreIndex] = {}
    _lock = asyncio.Lock()
    _openai_embed_model = None
    _hf_embed_model = None

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
            if chat_index and not chat_index.need_update:
                path_to_index = os.path.join(settings.MEDIA_ROOT, chat_uuid, 'index')
                storage_context = await sync_to_async(StorageContext.from_defaults,
                                                      thread_sensitive=False)(persist_dir=path_to_index)
                embed_model = await cls.get_embed_model()
                index = load_index_from_storage(storage_context=storage_context, embed_model=embed_model)
                if not chat_index.need_update:
                    cls._indexes[chat_uuid] = index
                    return cls._indexes[chat_uuid]
                else:
                    documents = await cls.get_documents_for_chat(chat_uuid)
                    pipeline = IngestionPipeline(
                        docstore=index.docstore,
                        vector_store=index.vector_store,
                        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
                        transformations=[embed_model],
                    )
                    nodes = await pipeline.arun(documents=documents)
                    chat_index.need_update = False
                    await sync_to_async(chat_index.save)()
                    await sync_to_async(storage_context.persist, thread_sensitive=False)(path_to_index)
                    cls._indexes[chat_uuid] = index
                    return cls._indexes[chat_uuid]

            documents = await cls.get_documents_for_chat(chat_uuid)

            docstore = SimpleDocumentStore()
            vector_store = SimpleVectorStore()
            storage_context = StorageContext.from_defaults(docstore=docstore, vector_store=vector_store)
            embed_model = await cls.get_embed_model()
            index = await sync_to_async(VectorStoreIndex.from_documents, thread_sensitive=False)(
                documents,
                storage_context=storage_context,
                embed_model=embed_model,
            )

            path_to_store_index = os.path.join(settings.MEDIA_ROOT, chat_uuid, 'index')
            await sync_to_async(storage_context.persist, thread_sensitive=False)(path_to_store_index)
            await sync_to_async(ChatIndex.objects.get_or_create)(chat_id=chat_uuid)
            cls._indexes[chat_uuid] = index
            return cls._indexes[chat_uuid]

    @classmethod
    async def get_embed_model(cls, use_openai: bool = False):
        if use_openai:
            if cls._openai_embed_model is None:
                cls._openai_embed_model = OpenAIEmbedding()
            return cls._openai_embed_model
        else:
            if cls._hf_embed_model is None:
                cls._hf_embed_model = HuggingFaceEmbedding(
                    model_name="BAAI/bge-m3",
                    max_length=8192
                )
            return cls._hf_embed_model

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
    @sync_to_async(thread_sensitive=False)
    def _load_files_sync(cls, filepaths):
        return SimpleDirectoryReader(input_files=filepaths, filename_as_id=True).load_data()
