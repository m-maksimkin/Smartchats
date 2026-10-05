import asyncio
import logging
import shutil
from pathlib import Path

from django.conf import settings
from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.memory import Memory
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

from ..models import ChatIndex
from .documents import load_documents_for_chat
from .llm_factory import build_llm, configure_llama_settings, get_embed_model
from .prompts import CONDENSE_PROMPT, CONTEXT_PROMPT
from .vector_store import chat_docstore, get_vector_store

logger = logging.getLogger(__name__)

_ingest_locks: dict[str, asyncio.Lock] = {}


def _remove_legacy_index_files(chat_uuid):
    index_dir = Path(settings.MEDIA_ROOT) / str(chat_uuid) / 'index'
    if index_dir.exists():
        shutil.rmtree(index_dir)


async def ensure_chat_index(chat_uuid):
    configure_llama_settings()
    lock = _ingest_locks.setdefault(str(chat_uuid), asyncio.Lock())
    async with lock:
        try:
            chat_index = await ChatIndex.objects.aget(chat_id=chat_uuid)
        except ChatIndex.DoesNotExist:
            chat_index = None
        if chat_index is not None and not chat_index.need_update:
            return

        documents = await load_documents_for_chat(chat_uuid)
        _remove_legacy_index_files(chat_uuid)
        pipeline = IngestionPipeline(
            transformations=[SentenceSplitter(), get_embed_model()],
            vector_store=get_vector_store(),
            docstore=chat_docstore(chat_uuid),
            docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
        )
        await pipeline.arun(documents=documents)
        if chat_index is None:
            await ChatIndex.objects.acreate(chat_id=chat_uuid, need_update=False)
        else:
            chat_index.need_update = False
            await chat_index.asave(update_fields=['need_update', 'updated'])
        logger.info('Stored embeddings for chat %s', chat_uuid)


def build_chat_engine(chat_settings):
    configure_llama_settings()
    index = VectorStoreIndex.from_vector_store(
        get_vector_store(),
        embed_model=get_embed_model(),
    )
    retriever = index.as_retriever(
        similarity_top_k=chat_settings.similarity_top_k,
        filters=MetadataFilters(filters=[
            MetadataFilter(key='chat_id', value=str(chat_settings.chat_id)),
        ]),
    )
    return CondensePlusContextChatEngine.from_defaults(
        retriever=retriever,
        llm=build_llm(chat_settings),
        memory=Memory.from_defaults(token_limit=settings.CHAT_MEMORY_TOKEN_LIMIT),
        system_prompt=chat_settings.instructions,
        context_prompt=CONTEXT_PROMPT,
        condense_prompt=CONDENSE_PROMPT,
        skip_condense=not chat_settings.rewrite_followups,
        node_postprocessors=[
            SimilarityPostprocessor(similarity_cutoff=chat_settings.similarity_cutoff),
        ],
    )
