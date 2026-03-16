from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from accounts.permissions import IsDriverOrLogist


class ChatRoomListView(generics.ListAPIView):
    """GET /api/chat/rooms/ — список кімнат поточного користувача."""
    permission_classes = [IsDriverOrLogist]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        from accounts.models import Role
        if user.role == Role.DRIVER:
            return ChatRoom.objects.filter(driver=user).select_related('driver', 'logist').prefetch_related('messages')
        elif user.role == Role.LOGIST:
            return ChatRoom.objects.filter(logist=user).select_related('driver', 'logist').prefetch_related('messages')
        return ChatRoom.objects.none()


class ChatRoomCreateView(generics.CreateAPIView):
    """POST /api/chat/rooms/ — логіст створює кімнату з водієм."""
    permission_classes = [IsDriverOrLogist]
    serializer_class = ChatRoomSerializer

    def create(self, request, *args, **kwargs):
        from accounts.models import User, Role
        driver_id = request.data.get('driver_id')
        logist_id = request.data.get('logist_id')

        # Логіст може створити кімнату зі своїм водієм
        if request.user.role == Role.LOGIST:
            logist_id = request.user.id
        elif request.user.role == Role.DRIVER:
            driver_id = request.user.id

        room, created = ChatRoom.objects.get_or_create(
            driver_id=driver_id,
            logist_id=logist_id,
        )
        return Response(
            ChatRoomSerializer(room, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ChatMessagesView(generics.ListAPIView):
    """GET /api/chat/rooms/<room_id>/messages/ — повідомлення кімнати."""
    permission_classes = [IsDriverOrLogist]
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        user = self.request.user
        # Перевіряємо доступ
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Message.objects.none()
        if room.driver != user and room.logist != user:
            return Message.objects.none()
        # Позначаємо як прочитані
        Message.objects.filter(room=room, is_read=False).exclude(sender=user).update(is_read=True)
        return Message.objects.filter(room=room).select_related('sender').order_by('created_at')
