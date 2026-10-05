from django.conf import settings
from llama_index.llms.openai.utils import O1_MODELS

from ..models import ChatSettings


def is_reasoning_model(model):
    return model in O1_MODELS


def _configured_models():
    models = list(settings.CHAT_MODEL_CHOICES)
    if settings.OPENAI_MODEL not in {value for value, _label in models}:
        models.insert(0, (settings.OPENAI_MODEL, settings.OPENAI_MODEL))
    return models


def model_choices():
    return [
        {'value': value, 'label': label, 'reasoning': is_reasoning_model(value)}
        for value, label in _configured_models()
    ]


def allowed_model_names():
    return {value for value, _label in _configured_models()}


def reasoning_effort_choices():
    return [
        {'value': value, 'label': label}
        for value, label in ChatSettings.ReasoningEffort.choices
    ]


def get_chat_settings(chat):
    chat_settings, _created = ChatSettings.objects.get_or_create(chat=chat)
    return chat_settings


async def aget_chat_settings(chat_uuid):
    try:
        return await ChatSettings.objects.aget(chat_id=chat_uuid)
    except ChatSettings.DoesNotExist:
        return await ChatSettings.objects.acreate(chat_id=chat_uuid)
