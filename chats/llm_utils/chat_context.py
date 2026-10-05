import asyncio
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from llama_index.core import (Settings, StorageContext, VectorStoreIndex,
                              load_index_from_storage)
from llama_index.core.ingestion import DocstoreStrategy
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.simple import SimpleVectorStore

from ..models import ChatIndex
from .delete_safe_ingestion_pipeline import DeleteSafeIngestionPipeline
from .documents import index_directory, load_documents_for_chat
from .llm_factory import configure_llama_settings, get_embed_model

logger = logging.getLogger(__name__)


class IndexManager:
    _indexes: dict[str, VectorStoreIndex] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_load_or_create_index(cls, chat_uuid):
        configure_llama_settings()
        async with cls._lock:
            try:
                chat_index = await sync_to_async(ChatIndex.objects.get)(chat_id=chat_uuid)
            except ChatIndex.DoesNotExist:
                chat_index = None
            if chat_index:
                return await cls._load_or_update_index(chat_uuid, chat_index)

            return await cls._create_index(chat_uuid)

    @classmethod
    async def _load_or_update_index(cls, chat_uuid, chat_index):
        index = cls._indexes.get(chat_uuid)
        if index is not None and not chat_index.need_update:
            logger.info(f'Retrieved index from IndexManager for chat {chat_uuid}')
            return index
        if index is not None:
            del cls._indexes[chat_uuid]
            logger.info(f'Deleted outdated index from IndexManager for chat {chat_uuid}')

        path_to_index = index_directory(settings.MEDIA_ROOT, chat_uuid)
        storage_context = await sync_to_async(
            StorageContext.from_defaults, thread_sensitive=False,
        )(persist_dir=path_to_index)
        embed_model = get_embed_model()
        index = await sync_to_async(load_index_from_storage, thread_sensitive=False)(
            storage_context=storage_context,
            embed_model=embed_model,
        )
        logger.info(f'Loaded index from disk for chat {chat_uuid}')
        if not chat_index.need_update:
            cls._indexes[chat_uuid] = index
            return index

        logger.info(f'Updating index for chat {chat_uuid}')
        documents = await load_documents_for_chat(chat_uuid)
        nodes = await cls._run_pipeline(index.docstore, index.vector_store, documents, embed_model)
        index.insert_nodes(nodes)
        chat_index.need_update = False
        await sync_to_async(chat_index.save)()
        await sync_to_async(storage_context.persist, thread_sensitive=False)(path_to_index)
        cls._indexes[chat_uuid] = index
        return index

    @classmethod
    async def _create_index(cls, chat_uuid):
        documents = await load_documents_for_chat(chat_uuid)
        docstore = SimpleDocumentStore()
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(docstore=docstore, vector_store=vector_store)
        embed_model = get_embed_model()
        nodes = await cls._run_pipeline(docstore, vector_store, documents, embed_model)
        index = await sync_to_async(VectorStoreIndex, thread_sensitive=True)(
            nodes,
            storage_context=storage_context,
            embed_model=embed_model,
        )
        path_to_store_index = index_directory(settings.MEDIA_ROOT, chat_uuid)
        await sync_to_async(storage_context.persist, thread_sensitive=False)(path_to_store_index)
        await sync_to_async(ChatIndex.objects.get_or_create)(chat_id=chat_uuid)
        cls._indexes[chat_uuid] = index
        logger.info(f'Created index for chat {chat_uuid}')
        return index

    @staticmethod
    async def _run_pipeline(docstore, vector_store, documents, embed_model):
        pipeline = DeleteSafeIngestionPipeline(
            docstore=docstore,
            vector_store=vector_store,
            docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
            transformations=[*Settings.transformations, embed_model],
        )
        return await pipeline.arun(documents=documents)
