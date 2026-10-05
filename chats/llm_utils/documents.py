from asgiref.sync import sync_to_async
from llama_index.core import Document, SimpleDirectoryReader

from ..models import ChatFile, ChatText, ChatURL


async def load_documents_for_chat(chat_uuid):
    documents = []
    texts = ChatText.objects.filter(chat=chat_uuid)
    async for text in texts:
        documents.append(Document(
            text=text.question + '\n' + text.answer,
            id_=f'text_{text.id}',
        ))

    chat_files_paths = []
    async for chat_file in ChatFile.objects.filter(chat=chat_uuid):
        chat_files_paths.append(chat_file.file.path)
    if chat_files_paths:
        file_documents = await _load_files_sync(chat_files_paths)
        documents.extend(file_documents)

    chat_urls = ChatURL.objects.filter(chat=chat_uuid)
    async for chat_url in chat_urls:
        documents.append(Document(text=chat_url.url_text, id_=f'url_{chat_url.id}'))

    chat_id = str(chat_uuid)
    for document in documents:
        document.metadata['chat_id'] = chat_id
    return documents


@sync_to_async(thread_sensitive=False)
def _load_files_sync(filepaths):
    return SimpleDirectoryReader(input_files=filepaths, filename_as_id=True).load_data()
