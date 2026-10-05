import logging
from urllib.parse import quote_plus

from django.conf import settings
from llama_index.storage.docstore.postgres import PostgresDocumentStore
from llama_index.storage.kvstore.postgres import PostgresKVStore
from llama_index.vector_stores.postgres import PGVectorStore

logger = logging.getLogger(__name__)

_vector_store = None


def _connection_strings():
    database = settings.DATABASES['default']
    user = quote_plus(database['USER'])
    password = quote_plus(database['PASSWORD'] or '')
    location = f"{user}:{password}@{database['HOST']}:{database['PORT']}/{database['NAME']}"
    return (
        f"postgresql+psycopg2://{location}",
        f"postgresql+asyncpg://{location}",
    )


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        sync_url, async_url = _connection_strings()
        _vector_store = PGVectorStore.from_params(
            connection_string=sync_url,
            async_connection_string=async_url,
            table_name='chat_embeddings',
            embed_dim=settings.OPENAI_EMBED_DIM,
            use_jsonb=True,
            indexed_metadata_keys={('chat_id', 'text')},
            hnsw_kwargs={
                'hnsw_m': 16,
                'hnsw_ef_construction': 64,
                'hnsw_ef_search': 40,
                'hnsw_dist_method': 'vector_cosine_ops',
            },
        )
    return _vector_store


def chat_docstore(chat_uuid):
    sync_url, async_url = _connection_strings()
    kv_store = PostgresKVStore.from_params(
        connection_string=sync_url,
        async_connection_string=async_url,
        table_name='chat_docstore',
        use_jsonb=True,
    )
    return PostgresDocumentStore(kv_store, namespace=str(chat_uuid))


def delete_chat_vectors(chat_uuid):
    chat_id = str(chat_uuid)
    store = get_vector_store()
    try:
        store._initialize()
        from sqlalchemy import delete
        with store._session() as session, session.begin():
            statement = delete(store._table_class).where(
                store._table_class.metadata_['chat_id'].astext == chat_id
            )
            session.execute(statement)
    except Exception:
        logger.warning('Could not delete vectors for chat %s', chat_id, exc_info=True)

    try:
        sync_url, async_url = _connection_strings()
        kv_store = PostgresKVStore.from_params(
            connection_string=sync_url,
            async_connection_string=async_url,
            table_name='chat_docstore',
            perform_setup=False,
            use_jsonb=True,
        )
        kv_store._initialize()
        from sqlalchemy import delete
        with kv_store._session() as session, session.begin():
            statement = delete(kv_store._table_class).where(
                kv_store._table_class.namespace.startswith(f'{chat_id}/')
            )
            session.execute(statement)
    except Exception:
        logger.warning('Could not delete document hashes for chat %s', chat_id, exc_info=True)
