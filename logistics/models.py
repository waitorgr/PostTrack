from django.db import models
from django.utils import timezone


class RouteStatus(models.TextChoices):
    DRAFT = 'draft', 'Чернетка'
    CONFIRMED = 'confirmed', 'Підтверджено'
    IN_PROGRESS = 'in_progress', 'Виконується'
    COMPLETED = 'completed', 'Виконано'
    CANCELLED = 'cancelled', 'Скасовано'


class Route(models.Model):
    driver = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='routes', verbose_name='Водій'
    )
    dispatch_group = models.ForeignKey(
        'dispatch.DispatchGroup', on_delete=models.CASCADE,
        related_name='routes', verbose_name='Dispatch група'
    )
    origin = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='outgoing_routes', verbose_name='Звідки'
    )
    destination = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='incoming_routes', verbose_name='Куди'
    )
    status = models.CharField(
        'Статус', max_length=20, choices=RouteStatus.choices, default=RouteStatus.DRAFT
    )
    is_auto = models.BooleanField('Авто-маршрут', default=False)
    scheduled_departure = models.DateTimeField('Запланований виїзд')
    notes = models.TextField('Нотатки', blank=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_routes'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'
        ordering = ['-created_at']

    def __str__(self):
        return f"Маршрут {self.dispatch_group.code} → {self.driver.full_name}"
