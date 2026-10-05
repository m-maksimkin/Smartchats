from dataclasses import asdict
from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from ninja.security import django_auth

from .llm_utils.prompts import INSTRUCTION_PRESETS
from .models import SmartChat
from .schemas import ChatSettingsIn, ChatSettingsResponse
from .services.chat_settings import (get_chat_settings, model_choices,
                                     reasoning_effort_choices)

api = NinjaAPI(
    title='Smartchats',
    urls_namespace='api',
    auth=django_auth,
    docs_url='/docs' if settings.DEBUG else None,
)

SETTINGS_FIELDS = tuple(name for name in ChatSettingsIn.model_fields if name != 'name')


def _owned_chat(request, chat_uuid):
    return get_object_or_404(SmartChat, id=chat_uuid, owner=request.user)


def _settings_response(chat, chat_settings):
    data = {field: getattr(chat_settings, field) for field in SETTINGS_FIELDS}
    data['name'] = chat.name
    data['updated'] = chat_settings.updated.isoformat()
    return {
        'settings': data,
        'options': {
            'models': model_choices(),
            'reasoning_efforts': reasoning_effort_choices(),
            'presets': [asdict(preset) for preset in INSTRUCTION_PRESETS],
        },
    }


@api.get('/chats/{chat_uuid}/settings', response=ChatSettingsResponse)
def read_chat_settings(request, chat_uuid: UUID):
    chat = _owned_chat(request, chat_uuid)
    return _settings_response(chat, get_chat_settings(chat))


@api.put('/chats/{chat_uuid}/settings', response=ChatSettingsResponse)
def update_chat_settings(request, chat_uuid: UUID, payload: ChatSettingsIn):
    chat = _owned_chat(request, chat_uuid)
    chat_settings = get_chat_settings(chat)
    for field in SETTINGS_FIELDS:
        setattr(chat_settings, field, getattr(payload, field))
    chat_settings.save()
    if chat.name != payload.name:
        chat.name = payload.name
        chat.save(update_fields=['name', 'updated'])
    return _settings_response(chat, chat_settings)
