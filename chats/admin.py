from django.contrib import admin

from .models import ChatFile, ChatIndex, ChatSettings, ChatText, ChatURL, SmartChat


class SmartChatAdmin(admin.ModelAdmin):
    pass


class ChatFileAdmin(admin.ModelAdmin):
    pass


class ChatTextAdmin(admin.ModelAdmin):
    pass


class ChatURLAdmin(admin.ModelAdmin):
    pass


class ChatIndexAdmin(admin.ModelAdmin):
    pass


class ChatSettingsAdmin(admin.ModelAdmin):
    list_display = ('chat', 'model', 'updated')


admin.site.register(SmartChat, SmartChatAdmin)
admin.site.register(ChatFile, ChatFileAdmin)
admin.site.register(ChatText, ChatTextAdmin)
admin.site.register(ChatURL, ChatURLAdmin)
admin.site.register(ChatIndex, ChatIndexAdmin)
admin.site.register(ChatSettings, ChatSettingsAdmin)
