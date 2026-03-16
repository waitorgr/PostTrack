from rest_framework import serializers
from .models import ChatRoom, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True, default=None)
    is_own = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'text', 'sender', 'sender_name', 'is_own', 'is_read', 'created_at']

    def get_is_own(self, obj):
        request = self.context.get('request')
        if request:
            return obj.sender_id == request.user.id
        return False


class ChatRoomSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    logist_name = serializers.CharField(source='logist.full_name', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'driver', 'driver_name', 'logist', 'logist_name',
                  'last_message', 'unread_count', 'created_at']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {'text': msg.text, 'created_at': msg.created_at}
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
