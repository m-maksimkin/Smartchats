from django.contrib import admin
from .models import SmartChat, ChatFile


class SmartChatAdmin(admin.ModelAdmin):
    pass


admin.site.register(SmartChat, SmartChatAdmin)
