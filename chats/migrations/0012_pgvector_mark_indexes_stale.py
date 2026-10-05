from django.db import migrations


def mark_indexes_stale(apps, schema_editor):
    ChatIndex = apps.get_model('chats', 'ChatIndex')
    ChatIndex.objects.all().update(need_update=True)


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0011_chatindex'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(mark_indexes_stale, migrations.RunPython.noop),
    ]
