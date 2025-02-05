import os.path
import asyncio
import logging

from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.conf import settings

from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader,\
    StorageContext, load_index_from_storage, ChatPromptTemplate
from llama_index.core.callbacks import CallbackManager
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.simple import SimpleVectorStore
from llama_index.core.prompts import PromptTemplate, ChatMessage
from llama_index.llms.openai import OpenAI

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from .custom_llama_logger import CustomLlamaInfoHandler
from .delete_safe_ingestion_pipeline import DeleteSafeIngestionPipeline
from ..models import SmartChat, ChatIndex, ChatText, ChatURL, ChatFile


logger = logging.getLogger(__name__)
llama_info_handler = CustomLlamaInfoHandler(logger=logger)
Settings.llm = OpenAI(model="gpt-4o-mini-2024-07-18")
Settings.callback_manager = CallbackManager(handlers=[llama_info_handler])


TEXT_QA_TEMPLATE_MESSAGES = [
    ChatMessage(
        role="system",
        content=(
            "Вы - экспертная система вопросов и ответов, которой доверяют во всем мире.\n"
            "Всегда отвечайте на запрос, используя предоставленную контекстную информацию, "
            "а не предыдущие знания.\n"
            "Вот некоторые правила, которым нужно следовать:\n"
            "1. Никогда не ссылайтесь напрямую на предоставленный контекст в своем ответе.\n"
            "2. Избегайте таких выражений, как 'Основываясь на контексте, ...' или "
            "'Контекстная информация ...' или чего-либо подобного."
        ),
    ),
    ChatMessage(
        role="user",
        content=(
            "Контекстная информация приведена ниже.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Учитывая контекстную информацию и не используя предыдущие знания, "
            "ответьте на запрос.\n"
            "Запрос: {query_str}\n"
            "Ответ: "
        ),
    ),
]


class IndexManager:
    _indexes: dict[str, VectorStoreIndex] = {}
    _lock = asyncio.Lock()
    _openai_embed_model = None
    _hf_embed_model = None

    @classmethod
    async def get_load_or_create_index(cls, chat_uuid, session_key):
        async with cls._lock:
            try:
                chat_index = await sync_to_async(ChatIndex.objects.get)(chat_id=chat_uuid)
            except ChatIndex.DoesNotExist:
                chat_index = None
            if chat_index:
                index = cls._indexes.get(chat_uuid)
                if index is not None:
                    if not chat_index.need_update:
                        logger.info(f'Retrieved index from IndexManager for chat {chat_uuid}')
                        return index
                    else:
                        del cls._indexes[chat_uuid]
                        logger.info(f'Deleted outdated index from IndexManager for chat {chat_uuid}')

                path_to_index = os.path.join(settings.MEDIA_ROOT, chat_uuid, 'index')
                storage_context = await sync_to_async(StorageContext.from_defaults,
                                                      thread_sensitive=False)(persist_dir=path_to_index)
                embed_model = await cls.get_embed_model()
                index = load_index_from_storage(storage_context=storage_context, embed_model=embed_model)
                logger.info(f'Loaded index from disk for chat {chat_uuid}')
                if not chat_index.need_update:
                    cls._indexes[chat_uuid] = index
                    return cls._indexes[chat_uuid]

                else:
                    logger.info(f'Updating index for chat {chat_uuid}')
                    documents = await cls.get_documents_for_chat(chat_uuid)
                    pipeline = DeleteSafeIngestionPipeline(
                        docstore=index.docstore,
                        vector_store=index.vector_store,
                        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
                        transformations=[*Settings.transformations, embed_model],
                    )
                    nodes = await pipeline.arun(documents=documents)
                    index.insert_nodes(nodes)
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
            pipeline = DeleteSafeIngestionPipeline(
                docstore=docstore,
                vector_store=vector_store,
                docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
                transformations=[*Settings.transformations, embed_model],
            )
            nodes = await pipeline.arun(documents=documents)
            index = await sync_to_async(VectorStoreIndex, thread_sensitive=True)(
                nodes,
                storage_context=storage_context,
                embed_model=embed_model,
            )

            path_to_store_index = os.path.join(settings.MEDIA_ROOT, chat_uuid, 'index')
            await sync_to_async(storage_context.persist, thread_sensitive=False)(path_to_store_index)
            await sync_to_async(ChatIndex.objects.get_or_create)(chat_id=chat_uuid)
            cls._indexes[chat_uuid] = index
            logger.info(f'Created index for chat {chat_uuid}')
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


def get_chat_prompt_templates(chat_uuid):
    chat_prompts = {'text_qa_template': ChatPromptTemplate.from_messages(message_templates=TEXT_QA_TEMPLATE_MESSAGES)}
    #  load chat specific system prompt
    return chat_prompts
