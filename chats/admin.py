from django.contrib import admin
from .models import SmartChat, ChatFile, ChatText, ChatURL


class SmartChatAdmin(admin.ModelAdmin):
    pass


class ChatFileAdmin(admin.ModelAdmin):
    pass


class ChatTextAdmin(admin.ModelAdmin):
    pass


class ChatURLAdmin(admin.ModelAdmin):
    pass


admin.site.register(SmartChat, SmartChatAdmin)
admin.site.register(ChatFile, ChatFileAdmin)
admin.site.register(ChatText, ChatTextAdmin)
admin.site.register(ChatURL, ChatURLAdmin)
