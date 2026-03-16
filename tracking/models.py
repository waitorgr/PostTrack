from django.db import models
from django.utils import timezone


class TrackingEvent(models.Model):
    EVENT_TYPES = [
        ('accepted', 'Прийнято'),
        ('picked_up_by_driver', 'Забрано водієм'),
        ('in_transit', 'В дорозі'),
        ('arrived_at_facility', 'Прибуло до об\'єкту'),
        ('sorted', 'Відсортовано'),
        ('out_for_delivery', 'Передано для доставки'),
        ('available_for_pickup', 'Очікує отримання'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
        ('returned', 'Повернуто'),
        ('note', 'Нотатка'),
    ]

    shipment = models.ForeignKey(
        'shipments.Shipment', on_delete=models.CASCADE, related_name='events'
    )
    event_type = models.CharField('Тип події', max_length=30, choices=EVENT_TYPES)
    location = models.ForeignKey(
        'locations.Location', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tracking_events'
    )
    note = models.TextField('Нотатка', blank=True)
    is_public = models.BooleanField('Публічна', default=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tracking_events'
    )
    created_at = models.DateTimeField('Час події', default=timezone.now)

    class Meta:
        verbose_name = 'Подія відстеження'
        verbose_name_plural = 'Події відстеження'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shipment.tracking_number} — {self.get_event_type_display()}"
