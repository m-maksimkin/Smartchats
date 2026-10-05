import json
from types import SimpleNamespace
from unittest import mock

from asgiref.sync import async_to_sync
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from .llm_utils.llm_factory import llm_kwargs
from .llm_utils.prompts import DEFAULT_INSTRUCTIONS
from .models import ChatSettings, SmartChat
from .routing import websocket_urlpatterns


def make_user(email):
    return get_user_model().objects.create_user(email=email, password='password')


def settings_payload(**changes):
    payload = {
        'name': 'Поддержка',
        'instructions': 'Отвечайте коротко.',
        'model': 'gpt-4.1-mini',
        'temperature': 0.4,
        'reasoning_effort': 'medium',
        'max_output_tokens': 800,
        'similarity_top_k': 4,
        'similarity_cutoff': 0.3,
        'rewrite_followups': False,
        'display_name': 'Ассистент',
        'welcome_message': 'Привет!',
        'suggested_messages': ['Цены', '  ', 'Доставка'],
        'input_placeholder': 'Ваш вопрос',
        'accent_color': '#ff6600',
    }
    payload.update(changes)
    return payload


class ChatSettingsApiTests(TestCase):

    def setUp(self):
        self.owner = make_user('owner@example.com')
        self.chat = SmartChat.objects.create(owner=self.owner, name='Chat')
        self.url = f'/api/chats/{self.chat.id}/settings'
        self.client.force_login(self.owner)

    def put(self, payload, client=None):
        return (client or self.client).put(
            self.url, data=json.dumps(payload), content_type='application/json',
        )

    def test_get_returns_defaults_and_options(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['settings']['instructions'], DEFAULT_INSTRUCTIONS)
        self.assertEqual(body['settings']['name'], 'Chat')
        models = {model['value']: model['reasoning'] for model in body['options']['models']}
        self.assertTrue(models['gpt-6-luna'])
        self.assertFalse(models['gpt-4.1-mini'])
        self.assertGreaterEqual(len(body['options']['presets']), 4)

    def test_put_saves_settings_and_chat_name(self):
        response = self.put(settings_payload())
        self.assertEqual(response.status_code, 200)
        chat_settings = ChatSettings.objects.get(chat=self.chat)
        self.assertEqual(chat_settings.model, 'gpt-4.1-mini')
        self.assertEqual(chat_settings.similarity_top_k, 4)
        self.assertEqual(chat_settings.suggested_messages, ['Цены', 'Доставка'])
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.name, 'Поддержка')

    def test_put_rejects_unknown_model_and_bad_color(self):
        response = self.put(settings_payload(model='gpt-unknown', accent_color='red'))
        self.assertEqual(response.status_code, 422)
        fields = {error['loc'][-1] for error in response.json()['detail']}
        self.assertEqual(fields, {'model', 'accent_color'})

    def test_other_user_gets_404(self):
        stranger = make_user('stranger@example.com')
        client = Client()
        client.force_login(stranger)
        self.assertEqual(client.get(self.url).status_code, 404)
        self.assertEqual(self.put(settings_payload(), client=client).status_code, 404)

    def test_anonymous_gets_401(self):
        self.assertEqual(Client().get(self.url).status_code, 401)

    def test_put_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(self.put(settings_payload(), client=client).status_code, 403)


class ChatPagesTests(TestCase):

    def setUp(self):
        self.owner = make_user('owner@example.com')
        self.client.force_login(self.owner)

    def test_new_chat_gets_settings_row(self):
        self.client.get(reverse('chats:initiate_chatbot_creation'))
        chat = SmartChat.objects.get(owner=self.owner)
        self.assertTrue(ChatSettings.objects.filter(chat=chat).exists())

    def test_settings_and_playground_pages_mount_islands(self):
        chat = SmartChat.objects.create(owner=self.owner)
        for name, root, entry in (
            ('chats:chat_settings', 'settings-root', 'src/entries/settings.tsx'),
            ('chats:chat_playground', 'playground-root', 'src/entries/playground.tsx'),
        ):
            response = self.client.get(reverse(name, kwargs={'chat_uuid': chat.id}))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'id="{root}"')
            self.assertContains(response, entry)
            self.assertIn('csrftoken', response.cookies)


class LlmKwargsTests(TestCase):

    def test_reasoning_model_uses_reasoning_effort(self):
        chat_settings = ChatSettings(model='gpt-6-luna', reasoning_effort='high',
                                     temperature=0.9, max_output_tokens=500)
        self.assertEqual(llm_kwargs(chat_settings), {
            'model': 'gpt-6-luna', 'reasoning_effort': 'high', 'max_tokens': 500,
        })

    def test_regular_model_uses_temperature(self):
        chat_settings = ChatSettings(model='gpt-4.1-mini', temperature=0.7, max_output_tokens=None)
        self.assertEqual(llm_kwargs(chat_settings), {'model': 'gpt-4.1-mini', 'temperature': 0.7})


class FakeStream:
    source_nodes = [
        SimpleNamespace(node=SimpleNamespace(metadata={'source': 'prices.pdf'})),
        SimpleNamespace(node=SimpleNamespace(metadata={'source': 'prices.pdf'})),
    ]

    async def async_response_gen(self):
        for token in ('Привет', ', мир'):
            yield token


class FakeEngine:
    async def astream_chat(self, message):
        return FakeStream()


class ChatConsumerTests(TestCase):

    def setUp(self):
        self.owner = make_user('owner@example.com')
        self.chat = SmartChat.objects.create(owner=self.owner)

    def communicator(self, user):
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, f'/ws/chats/{self.chat.id}/')
        communicator.scope['user'] = user
        return communicator

    def test_stranger_is_disconnected(self):
        stranger = make_user('stranger@example.com')

        async def run():
            communicator = self.communicator(stranger)
            await communicator.connect()
            output = await communicator.receive_output()
            await communicator.disconnect()
            return output

        self.assertEqual(async_to_sync(run)()['type'], 'websocket.close')

    @mock.patch('chats.consumers.build_chat_engine', return_value=FakeEngine())
    @mock.patch('chats.consumers.ensure_chat_index')
    def test_owner_receives_streamed_answer(self, ensure_chat_index, build_chat_engine):
        async def run():
            communicator = self.communicator(self.owner)
            await communicator.connect()
            frames = [await communicator.receive_json_from(), await communicator.receive_json_from()]
            await communicator.send_json_to({'type': 'message', 'text': 'Привет'})
            for _ in range(3):
                frames.append(await communicator.receive_json_from())
            await communicator.disconnect()
            return frames

        frames = async_to_sync(run)()
        self.assertEqual(frames[:2], [
            {'type': 'status', 'state': 'indexing'},
            {'type': 'status', 'state': 'ready'},
        ])
        self.assertEqual(frames[2:], [
            {'type': 'delta', 'text': 'Привет'},
            {'type': 'delta', 'text': ', мир'},
            {'type': 'done', 'sources': ['prices.pdf']},
        ])
        chat_settings = build_chat_engine.call_args.args[0]
        self.assertEqual(str(chat_settings.chat_id), str(self.chat.id))


class ChatSettingsMigrationTests(TransactionTestCase):

    def test_existing_chats_get_settings(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('chats', '0012_pgvector_mark_indexes_stale')])
        old_apps = executor.loader.project_state(
            [('chats', '0012_pgvector_mark_indexes_stale')]
        ).apps
        user = make_user('old@example.com')
        chat = old_apps.get_model('chats', 'SmartChat').objects.create(owner_id=user.id)

        executor = MigrationExecutor(connection)
        executor.migrate([('chats', '0013_chatsettings')])
        self.assertTrue(ChatSettings.objects.filter(chat_id=chat.id).exists())
