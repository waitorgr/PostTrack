from django.urls import path
from .views import ChatRoomListView, ChatRoomCreateView, ChatMessagesView

urlpatterns = [
    path('rooms/', ChatRoomListView.as_view()),
    path('rooms/create/', ChatRoomCreateView.as_view()),
    path('rooms/<int:room_id>/messages/', ChatMessagesView.as_view()),
]
