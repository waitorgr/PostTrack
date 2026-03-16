from django.db import models
from django.utils import timezone
import random
import string


def generate_tracking_number():
    digits = ''.join(random.choices(string.digits, k=9))
    return f"UA{digits}UA"


class ShipmentStatus(models.TextChoices):
    ACCEPTED = 'accepted', 'Прийнято'
    PICKED_UP_BY_DRIVER = 'picked_up_by_driver', 'Забрано водієм'
    IN_TRANSIT = 'in_transit', 'В дорозі'
    ARRIVED_AT_FACILITY = 'arrived_at_facility', 'Прибуло до об\'єкту'
    SORTED = 'sorted', 'Відсортовано'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Передано для доставки'
    AVAILABLE_FOR_PICKUP = 'available_for_pickup', 'Очікує отримання'
    DELIVERED = 'delivered', 'Доставлено'
    CANCELLED = 'cancelled', 'Скасовано'
    RETURNED = 'returned', 'Повернуто'


class PaymentType(models.TextChoices):
    PREPAID = 'prepaid', 'Передоплата'
    CASH_ON_DELIVERY = 'cash_on_delivery', 'Оплата при отриманні'


class Shipment(models.Model):
    tracking_number = models.CharField(
        'Трекінг-номер', max_length=20, unique=True, default=generate_tracking_number
    )
    # Відправник (фізична особа, не User)
    sender_first_name = models.CharField('Ім\'я відправника', max_length=100)
    sender_last_name = models.CharField('Прізвище відправника', max_length=100)
    sender_patronymic = models.CharField('По-батькові відправника', max_length=100)
    sender_phone = models.CharField('Телефон відправника', max_length=20)
    sender_email = models.EmailField('Email відправника', blank=True)

    # Отримувач
    receiver_first_name = models.CharField('Ім\'я отримувача', max_length=100)
    receiver_last_name = models.CharField('Прізвище отримувача', max_length=100)
    receiver_patronymic = models.CharField('По-батькові отримувача', max_length=100)
    receiver_phone = models.CharField('Телефон отримувача', max_length=20)
    receiver_email = models.EmailField('Email отримувача', blank=True)

    # Локації
    origin = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='sent_shipments', verbose_name='Відділення відправлення'
    )
    destination = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        related_name='received_shipments', verbose_name='Відділення призначення'
    )

    # Параметри
    weight = models.DecimalField('Вага (кг)', max_digits=7, decimal_places=2)
    description = models.TextField('Опис', blank=True)
    price = models.DecimalField('Ціна доставки', max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        'Тип оплати', max_length=20, choices=PaymentType.choices, default=PaymentType.PREPAID
    )

    # Статус
    status = models.CharField(
        'Статус', max_length=30, choices=ShipmentStatus.choices, default=ShipmentStatus.ACCEPTED
    )

    # Хто зареєстрував
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_shipments', verbose_name='Зареєстрував'
    )
    created_at = models.DateTimeField('Створено', default=timezone.now)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Посилка'
        verbose_name_plural = 'Посилки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} ({self.get_status_display()})"

    @property
    def sender_full_name(self):
        return f"{self.sender_last_name} {self.sender_first_name} {self.sender_patronymic}".strip()

    @property
    def receiver_full_name(self):
        return f"{self.receiver_last_name} {self.receiver_first_name} {self.receiver_patronymic}".strip()

    @staticmethod
    def calculate_price(weight_kg):
        """30 грн базово + 15 грн/кг."""
        return round(30 + 15 * float(weight_kg), 2)


class Payment(models.Model):
    shipment = models.OneToOneField(
        Shipment, on_delete=models.CASCADE, related_name='payment'
    )
    amount = models.DecimalField('Сума', max_digits=10, decimal_places=2)
    is_paid = models.BooleanField('Оплачено', default=False)
    paid_at = models.DateTimeField('Час оплати', null=True, blank=True)
    received_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_payments'
    )

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплати'

    def __str__(self):
        status = 'оплачено' if self.is_paid else 'не оплачено'
        return f"Оплата {self.shipment.tracking_number} — {status}"
