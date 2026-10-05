import logging

from django.conf import settings
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from ..services.chat_settings import is_reasoning_model
from .custom_llama_logger import CustomLlamaInfoHandler

logger = logging.getLogger(__name__)

_embed_model = None
_configured = False


def llm_kwargs(chat_settings):
    kwargs = {'model': chat_settings.model}
    if chat_settings.max_output_tokens:
        kwargs['max_tokens'] = chat_settings.max_output_tokens
    if is_reasoning_model(chat_settings.model):
        kwargs['reasoning_effort'] = chat_settings.reasoning_effort
    else:
        kwargs['temperature'] = chat_settings.temperature
    return kwargs


def build_llm(chat_settings):
    return OpenAI(**llm_kwargs(chat_settings))


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = OpenAIEmbedding(model=settings.OPENAI_EMBED_MODEL)
    return _embed_model


def configure_llama_settings():
    global _configured
    if _configured:
        return
    Settings.embed_model = get_embed_model()
    Settings.callback_manager = CallbackManager(
        handlers=[CustomLlamaInfoHandler(logger=logger)]
    )
    _configured = True
