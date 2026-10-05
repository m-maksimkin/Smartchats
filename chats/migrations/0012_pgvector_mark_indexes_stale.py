from django.db import migrations


def create_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS vector;')


def mark_indexes_stale(apps, schema_editor):
    ChatIndex = apps.get_model('chats', 'ChatIndex')
    ChatIndex.objects.all().update(need_update=True)


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0011_chatindex'),
    ]

    operations = [
        migrations.RunPython(create_vector_extension, migrations.RunPython.noop),
        migrations.RunPython(mark_indexes_stale, migrations.RunPython.noop),
    ]
