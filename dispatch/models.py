from django.db import models
from django.utils import timezone
import random
import string


def generate_group_code():
    while True:
        suffix = ''.join(random.choices(string.digits, k=6))
        code = f"DG-{suffix}"
        if not DispatchGroup.objects.filter(code=code).exists():
            return code


class DispatchGroupStatus(models.TextChoices):
    FORMING = 'forming', 'Формується'
    READY = 'ready', 'Готово до відправки'
    IN_TRANSIT = 'in_transit', 'В дорозі'
    ARRIVED = 'arrived', 'Прибуло'
    COMPLETED = 'completed', 'Завершено'


class DispatchGroup(models.Model):
    code = models.CharField('Код групи', max_length=20, unique=True, default=generate_group_code)
    status = models.CharField(
        'Статус', max_length=20, choices=DispatchGroupStatus.choices,
        default=DispatchGroupStatus.FORMING
    )
    origin = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='outgoing_groups', verbose_name='Звідки'
    )
    destination = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='incoming_groups', verbose_name='Куди'
    )
    driver = models.ForeignKey(
    'accounts.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='driver_groups',
    verbose_name='Водій'
    )
    current_location = models.ForeignKey(
        'locations.Location', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='current_groups',
        verbose_name='Поточна локація'
    )
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_groups', verbose_name='Створив'
    )
    departed_at = models.DateTimeField('Час відправки', null=True, blank=True)
    arrived_at = models.DateTimeField('Час прибуття', null=True, blank=True)
    created_at = models.DateTimeField('Створено', default=timezone.now)

    class Meta:
        verbose_name = 'Dispatch група'
        verbose_name_plural = 'Dispatch групи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.get_status_display()})"
    
    def get_destination_location(self):
        """Автоматично визначає куди має йти група на основі ієрархії"""
        if not self.origin:
            return None
        
        from locations.models import LocationType
        
        # Якщо origin - відділення пошти, то destination - його РЦ
        if self.origin.type == LocationType.POST_OFFICE:
            return self.origin.get_distribution_center()
        
        # Якщо origin - РЦ, то destination - його СЦ
        elif self.origin.type == LocationType.DISTRIBUTION_CENTER:
            return self.origin.get_sorting_center()
        
        # Сортувальні центри не створюють групи (або це міжрегіональний транспорт)
        return None


class DispatchGroupItem(models.Model):
    group = models.ForeignKey(DispatchGroup, on_delete=models.CASCADE, related_name='items')
    shipment = models.ForeignKey(
        'shipments.Shipment', on_delete=models.CASCADE, related_name='dispatch_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='added_items'
    )

    class Meta:
        unique_together = [['group', 'shipment']]
        verbose_name = 'Елемент Dispatch групи'
        verbose_name_plural = 'Елементи Dispatch груп'
