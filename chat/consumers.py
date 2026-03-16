import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Перевіряємо чи є доступ до цієї кімнати
        has_access = await self.check_access()
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Позначаємо всі непрочитані як прочитані
        await self.mark_messages_read()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('text', '').strip()
        if not message_text:
            return

        # Зберігаємо повідомлення в БД
        message = await self.save_message(message_text)

        # Надсилаємо всім у кімнаті
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message['id'],
                'text': message_text,
                'sender_id': self.user.id,
                'sender_name': self.user.full_name,
                'created_at': message['created_at'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['message_id'],
            'text': event['text'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'created_at': event['created_at'],
            'is_own': event['sender_id'] == self.user.id,
        }))

    @database_sync_to_async
    def check_access(self):
        from .models import ChatRoom
        from accounts.models import Role
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.driver == self.user or room.logist == self.user
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text):
        from .models import ChatRoom, Message
        room = ChatRoom.objects.get(id=self.room_id)
        msg = Message.objects.create(room=room, sender=self.user, text=text)
        return {
            'id': msg.id,
            'created_at': msg.created_at.isoformat(),
        }

    @database_sync_to_async
    def mark_messages_read(self):
        from .models import ChatRoom, Message
        Message.objects.filter(
            room_id=self.room_id,
            is_read=False,
        ).exclude(sender=self.user).update(is_read=True)
