import os

from asgiref.sync import sync_to_async
from llama_index.core import Document, SimpleDirectoryReader

from ..models import ChatFile, ChatText, ChatURL


async def load_documents_for_chat(chat_uuid):
    documents = []
    texts = ChatText.objects.filter(chat=chat_uuid)
    async for text in texts:
        documents.append(Document(
            text=text.question + '\n' + text.answer,
            id_=f'text_{str(text.id)}',
        ))

    chat_files_paths = []
    async for chat_file in ChatFile.objects.filter(chat=chat_uuid):
        chat_files_paths.append(chat_file.file.path)
    if chat_files_paths:
        file_documents = await _load_files_sync(chat_files_paths)
        documents.extend(file_documents)

    chat_urls = ChatURL.objects.filter(chat=chat_uuid)
    async for chat_url in chat_urls:
        documents.append(Document(text=chat_url.url_text, id_=f'url_{str(chat_url.id)}'))
    return documents


@sync_to_async(thread_sensitive=False)
def _load_files_sync(filepaths):
    return SimpleDirectoryReader(input_files=filepaths, filename_as_id=True).load_data()


def index_directory(media_root, chat_uuid):
    return os.path.join(media_root, str(chat_uuid), 'index')
