# Generated by Django 4.2.3 on 2023-10-09 23:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0005_chatfile_file_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='smartchat',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='ChatText',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(blank=True, db_index=True, default=None, max_length=1000, null=True)),
                ('answer', models.TextField(max_length=100000)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='texts', to='chats.smartchat')),
            ],
        ),
    ]
