from django.contrib import admin
from .models import SmartChat, ChatFile, ChatText


class SmartChatAdmin(admin.ModelAdmin):
    pass


class ChatFileAdmin(admin.ModelAdmin):
    pass


class ChatTextAdmin(admin.ModelAdmin):
    pass


admin.site.register(SmartChat, SmartChatAdmin)
admin.site.register(ChatFile, ChatFileAdmin)
admin.site.register(ChatText, ChatTextAdmin)
