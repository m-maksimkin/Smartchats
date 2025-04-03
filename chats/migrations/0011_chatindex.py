# Generated by Django 4.2.3 on 2024-12-09 09:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0010_remove_chaturl_url_html_response'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatIndex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('need_update', models.BooleanField(default=False)),
                ('index_dir', models.CharField(blank=True, default='', max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index', to='chats.smartchat')),
            ],
        ),
    ]
