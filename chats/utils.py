import requests
from urllib.parse import urlparse, urljoin, urldefrag, quote
from hashlib import md5
from bs4 import BeautifulSoup
from collections import deque
from .models import ChatURL
from django.core.files.base import ContentFile
from django.contrib import messages
import logging


logger = logging.getLogger(__name__)

FileExtensions = [
    '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc',
    '.docx', '.zip', '.rar', '.mp3',
]


def crawl_url(start_url, chat, request):
    visited = set()
    crawl_queue = deque()
    crawl_queue.append(start_url)
    # visited.add(start_url)
    netloc = urlparse(start_url).netloc
    while crawl_queue:
        url = crawl_queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            logger.info(f"Failed to crawl: {url}")
            continue
        if not r.status_code:
            continue
        # file_name = md5(url.encode()).hexdigest() + '.html'
        # content_file = ContentFile(r.content, name=file_name)  # add custom file name
        # chat_url = ChatURL(url=url, chat=chat, url_html_response=content_file)
        chat_url = ChatURL(url=url, chat=chat)
        soup = BeautifulSoup(r.content, features='lxml')
        url_text = soup.text
        url_text_len = len(url_text)
        if (chat.character_length + url_text_len
                > chat.owner.chatbot_character_limit):
            messages.error(
                request,
                "В процессе сбора данных превышен лимит доступных символов"
            )
            return
        chat_url.url_text = url_text
        chat_url.character_length = url_text_len
        chat.character_length += url_text_len
        chat_url.save()
        chat.save()

        for link in soup.find_all('a'):
            href = link.get('href')
            if href is not None:
                href = urljoin(url, href)
                href = urldefrag(href).url
                if (not any(href.endswith(ext) for ext in FileExtensions)
                        and urlparse(href).netloc == netloc
                        and href not in visited):
                    crawl_queue.append(href)
                    if len(visited) > 100:
                        messages.error(
                            request,
                            "Достигнут предел обработанных ссылок, "
                            "сбор данных был приостановлен."
                        )
                        return
    return

