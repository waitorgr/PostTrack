from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    """Кімната чату між конкретним водієм і логістом."""
    driver = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='chat_rooms_as_driver'
    )
    logist = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='chat_rooms_as_logist'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [['driver', 'logist']]
        verbose_name = 'Кімната чату'
        verbose_name_plural = 'Кімнати чату'

    def __str__(self):
        return f"Чат: {self.driver.full_name} ↔ {self.logist.full_name}"

    @property
    def room_name(self):
        return f"chat_{self.id}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='sent_messages'
    )
    text = models.TextField('Текст')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}"
