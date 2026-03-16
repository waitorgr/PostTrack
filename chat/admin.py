from django.contrib import admin
from .models import ChatRoom, Message
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['driver', 'logist', 'created_at']
