from asgiref.sync import sync_to_async
from llama_index.core import Document, SimpleDirectoryReader

from ..models import ChatFile, ChatText, ChatURL

HIDDEN_METADATA_KEYS = ['chat_id', 'source']


async def load_documents_for_chat(chat_uuid):
    documents = []
    texts = ChatText.objects.filter(chat=chat_uuid)
    async for text in texts:
        document = Document(
            text=text.question + '\n' + text.answer,
            id_=f'text_{text.id}',
        )
        document.metadata['source'] = text.question if text.is_question else 'Текст'
        documents.append(document)

    chat_files_paths = []
    async for chat_file in ChatFile.objects.filter(chat=chat_uuid):
        chat_files_paths.append(chat_file.file.path)
    if chat_files_paths:
        file_documents = await _load_files_sync(chat_files_paths)
        for document in file_documents:
            document.metadata['source'] = document.metadata.get('file_name', '')
        documents.extend(file_documents)

    chat_urls = ChatURL.objects.filter(chat=chat_uuid)
    async for chat_url in chat_urls:
        document = Document(text=chat_url.url_text, id_=f'url_{chat_url.id}')
        document.metadata['source'] = chat_url.url
        documents.append(document)

    chat_id = str(chat_uuid)
    for document in documents:
        document.metadata['chat_id'] = chat_id
        document.excluded_embed_metadata_keys = [
            *document.excluded_embed_metadata_keys, *HIDDEN_METADATA_KEYS,
        ]
        document.excluded_llm_metadata_keys = [
            *document.excluded_llm_metadata_keys, *HIDDEN_METADATA_KEYS,
        ]
    return documents


@sync_to_async(thread_sensitive=False)
def _load_files_sync(filepaths):
    return SimpleDirectoryReader(input_files=filepaths, filename_as_id=True).load_data()
