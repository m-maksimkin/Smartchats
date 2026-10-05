import logging

from django.conf import settings
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from .custom_llama_logger import CustomLlamaInfoHandler

logger = logging.getLogger(__name__)

_llm = None
_embed_model = None
_configured = False


def get_llm():
    global _llm
    if _llm is None:
        _llm = OpenAI(model=settings.OPENAI_MODEL)
    return _llm


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = OpenAIEmbedding(model=settings.OPENAI_EMBED_MODEL)
    return _embed_model


def configure_llama_settings():
    global _configured
    if _configured:
        return
    Settings.llm = get_llm()
    Settings.embed_model = get_embed_model()
    Settings.callback_manager = CallbackManager(
        handlers=[CustomLlamaInfoHandler(logger=logger)]
    )
    _configured = True
