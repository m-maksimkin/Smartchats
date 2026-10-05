from typing import Literal, Optional

from ninja import Schema
from pydantic import Field, field_validator

from .services.chat_settings import allowed_model_names

HEX_COLOR = r'^#[0-9a-fA-F]{6}$'
ReasoningEffort = Literal['none', 'low', 'medium', 'high']


class ChatSettingsFields(Schema):
    name: str = Field(min_length=1, max_length=50)
    instructions: str = Field(min_length=1, max_length=10000)
    model: str
    temperature: float = Field(ge=0, le=1)
    reasoning_effort: ReasoningEffort
    max_output_tokens: Optional[int] = Field(default=None, ge=64, le=16000)
    similarity_top_k: int = Field(ge=1, le=10)
    similarity_cutoff: float = Field(ge=0, le=1)
    rewrite_followups: bool

    display_name: str = Field(default='', max_length=60)
    welcome_message: str = Field(default='', max_length=500)
    suggested_messages: list[str] = Field(default_factory=list, max_length=6)
    input_placeholder: str = Field(default='', max_length=120)
    accent_color: str = Field(pattern=HEX_COLOR)


class ChatSettingsIn(ChatSettingsFields):

    @field_validator('model')
    @classmethod
    def model_is_allowed(cls, value):
        if value not in allowed_model_names():
            raise ValueError('Модель недоступна')
        return value

    @field_validator('suggested_messages')
    @classmethod
    def clean_suggested_messages(cls, value):
        cleaned = [message.strip() for message in value if message.strip()]
        if any(len(message) > 120 for message in cleaned):
            raise ValueError('Подсказка длиннее 120 символов')
        return cleaned


class ChatSettingsOut(ChatSettingsFields):
    updated: str


class ModelChoice(Schema):
    value: str
    label: str
    reasoning: bool


class Choice(Schema):
    value: str
    label: str


class InstructionPresetOut(Schema):
    key: str
    title: str
    text: str


class SettingsOptions(Schema):
    models: list[ModelChoice]
    reasoning_efforts: list[Choice]
    presets: list[InstructionPresetOut]


class ChatSettingsResponse(Schema):
    settings: ChatSettingsOut
    options: SettingsOptions
