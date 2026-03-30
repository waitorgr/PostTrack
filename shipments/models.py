from decimal import Decimal, ROUND_HALF_UP
import random
import re
import string

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


TRACKING_PREFIX = "UA"
TRACKING_SUFFIX = "UA"
TRACKING_DIGITS_COUNT = 9
BASE_PRICE = Decimal("30.00")
PRICE_PER_KG = Decimal("15.00")
TWO_DECIMAL_PLACES = Decimal("0.01")


def generate_tracking_number():
    """
    Генерує унікальний трек-номер формату UA123456789UA.
    """
    while True:
        digits = "".join(random.choices(string.digits, k=TRACKING_DIGITS_COUNT))
        tracking_number = f"{TRACKING_PREFIX}{digits}{TRACKING_SUFFIX}"
        if not Shipment.objects.filter(tracking_number=tracking_number).exists():
            return tracking_number


class ShipmentStatus(models.TextChoices):
    ACCEPTED = "accepted", "Прийнято"
    PICKED_UP_BY_DRIVER = "picked_up_by_driver", "Забрано водієм"
    IN_TRANSIT = "in_transit", "В дорозі"
    ARRIVED_AT_FACILITY = "arrived_at_facility", "Прибуло до об'єкту"
    SORTED = "sorted", "Відсортовано"
    OUT_FOR_DELIVERY = "out_for_delivery", "Передано для доставки"
    AVAILABLE_FOR_PICKUP = "available_for_pickup", "Очікує отримання"
    DELIVERED = "delivered", "Доставлено"
    CANCELLED = "cancelled", "Скасовано"
    RETURNED = "returned", "Повернуто"


class PaymentType(models.TextChoices):
    PREPAID = "prepaid", "Передоплата"
    CASH_ON_DELIVERY = "cash_on_delivery", "Оплата при отриманні"


class Shipment(models.Model):
    tracking_number = models.CharField(
        "Трекінг-номер",
        max_length=20,
        unique=True,
        default=generate_tracking_number,
    )

    sender_first_name = models.CharField("Ім'я відправника", max_length=100)
    sender_last_name = models.CharField("Прізвище відправника", max_length=100)
    sender_patronymic = models.CharField("По-батькові відправника", max_length=100)
    sender_phone = models.CharField("Телефон відправника", max_length=20)
    sender_email = models.EmailField("Email відправника", blank=True)

    receiver_first_name = models.CharField("Ім'я отримувача", max_length=100)
    receiver_last_name = models.CharField("Прізвище отримувача", max_length=100)
    receiver_patronymic = models.CharField("По-батькові отримувача", max_length=100)
    receiver_phone = models.CharField("Телефон отримувача", max_length=20)
    receiver_email = models.EmailField("Email отримувача", blank=True)

    origin = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="sent_shipments",
        verbose_name="Відділення відправлення",
    )
    destination = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="received_shipments",
        verbose_name="Відділення призначення",
    )

    weight = models.DecimalField("Вага (кг)", max_digits=7, decimal_places=2)
    description = models.TextField("Опис", blank=True)
    price = models.DecimalField("Ціна доставки", max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        "Тип оплати",
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.PREPAID,
    )

    status = models.CharField(
        "Статус",
        max_length=30,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.ACCEPTED,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_shipments",
        verbose_name="Зареєстрував",
    )
    created_at = models.DateTimeField("Створено", default=timezone.now)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Посилка"
        verbose_name_plural = "Посилки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_number} ({self.get_status_display()})"

    @staticmethod
    def _normalize_name_part(value):
        return " ".join((value or "").split())

    @staticmethod
    def _normalize_phone(value):
        value = (value or "").strip()
        if value.startswith("+"):
            return "+" + re.sub(r"\D", "", value[1:])
        return re.sub(r"\D", "", value)

    @staticmethod
    def _validate_phone(value, field_name, errors):
        digits_only = re.sub(r"\D", "", value or "")
        if not digits_only:
            errors[field_name] = "Телефон є обов'язковим."
            return
        if len(digits_only) < 10 or len(digits_only) > 15:
            errors[field_name] = "Телефон має містити від 10 до 15 цифр."

    @property
    def sender_full_name(self):
        parts = [self.sender_last_name, self.sender_first_name, self.sender_patronymic]
        return " ".join(part for part in parts if part).strip()

    @property
    def receiver_full_name(self):
        parts = [self.receiver_last_name, self.receiver_first_name, self.receiver_patronymic]
        return " ".join(part for part in parts if part).strip()

    @classmethod
    def calculate_price(cls, weight_kg):
        """
        Базовий тариф: 30 грн + 15 грн за кожен кг.
        """
        if weight_kg is None:
            raise ValueError("Вага не може бути порожньою.")

        weight = Decimal(str(weight_kg))
        if weight <= 0:
            raise ValueError("Вага повинна бути більшою за 0.")

        total = BASE_PRICE + (weight * PRICE_PER_KG)
        return total.quantize(TWO_DECIMAL_PLACES, rounding=ROUND_HALF_UP)

    def clean(self):
        super().clean()
    
        from locations.models import Location, LocationType
    
        errors = {}
    
        self.sender_first_name = self._normalize_name_part(self.sender_first_name)
        self.sender_last_name = self._normalize_name_part(self.sender_last_name)
        self.sender_patronymic = self._normalize_name_part(self.sender_patronymic)
        self.receiver_first_name = self._normalize_name_part(self.receiver_first_name)
        self.receiver_last_name = self._normalize_name_part(self.receiver_last_name)
        self.receiver_patronymic = self._normalize_name_part(self.receiver_patronymic)
    
        self.sender_phone = self._normalize_phone(self.sender_phone)
        self.receiver_phone = self._normalize_phone(self.receiver_phone)
    
        self.sender_email = (self.sender_email or "").strip().lower()
        self.receiver_email = (self.receiver_email or "").strip().lower()
        self.description = (self.description or "").strip()
    
        required_name_fields = {
            "sender_first_name": self.sender_first_name,
            "sender_last_name": self.sender_last_name,
            "sender_patronymic": self.sender_patronymic,
            "receiver_first_name": self.receiver_first_name,
            "receiver_last_name": self.receiver_last_name,
            "receiver_patronymic": self.receiver_patronymic,
        }
        for field_name, value in required_name_fields.items():
            if not value:
                errors[field_name] = "Поле не може бути порожнім або складатися лише з пробілів."
    
        self._validate_phone(self.sender_phone, "sender_phone", errors)
        self._validate_phone(self.receiver_phone, "receiver_phone", errors)
    
        origin = None
        destination = None
    
        if self.origin_id:
            origin = Location.objects.filter(pk=self.origin_id).only("id", "type").first()
            if not origin:
                errors["origin"] = "Відділення відправлення не знайдено."
        else:
            errors["origin"] = "Відділення відправлення є обов'язковим."
    
        if self.destination_id:
            destination = Location.objects.filter(pk=self.destination_id).only("id", "type").first()
            if not destination:
                errors["destination"] = "Відділення призначення не знайдено."
        else:
            errors["destination"] = "Відділення призначення є обов'язковим."
    
        if origin and destination and origin.id == destination.id:
            errors["destination"] = "Відділення призначення має відрізнятися від відділення відправлення."
    
        if origin and origin.type != LocationType.POST_OFFICE:
            errors["origin"] = "Відділення відправлення має бути поштовим відділенням."
    
        if destination and destination.type != LocationType.POST_OFFICE:
            errors["destination"] = "Відділення призначення має бути поштовим відділенням."
    
        if self.weight is None:
            errors["weight"] = "Вага є обов'язковою."
        elif self.weight <= 0:
            errors["weight"] = "Вага повинна бути більшою за 0."
    
        if self.price is None:
            errors["price"] = "Ціна є обов'язковою."
        elif self.price < 0:
            errors["price"] = "Ціна не може бути від'ємною."
    
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = generate_tracking_number()

        if self.weight is not None and not self.price:
            self.price = self.calculate_price(self.weight)

        self.full_clean()
        return super().save(*args, **kwargs)


class Payment(models.Model):
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    amount = models.DecimalField("Сума", max_digits=10, decimal_places=2)
    is_paid = models.BooleanField("Оплачено", default=False)
    paid_at = models.DateTimeField("Час оплати", null=True, blank=True)
    received_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_payments",
    )

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплати"

    def __str__(self):
        status = "оплачено" if self.is_paid else "не оплачено"
        return f"Оплата {self.shipment.tracking_number} — {status}"

    def clean(self):
        super().clean()

        errors = {}

        if self.amount is None:
            errors["amount"] = "Сума є обов'язковою."
        elif self.amount <= 0:
            errors["amount"] = "Сума повинна бути більшою за 0."

        if self.shipment_id and self.amount is not None and self.amount != self.shipment.price:
            errors["amount"] = "Сума оплати повинна дорівнювати вартості доставки посилки."

        if self.is_paid and not self.paid_at:
            self.paid_at = timezone.now()

        if self.is_paid and not self.received_by and self.shipment.payment_type == PaymentType.CASH_ON_DELIVERY:
            errors["received_by"] = "Потрібно вказати працівника, який прийняв оплату."

        if not self.is_paid:
            self.paid_at = None
            self.received_by = None

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def mark_as_paid(self, received_by=None, paid_at=None, commit=True):
        self.is_paid = True
        self.received_by = received_by
        self.paid_at = paid_at or timezone.now()

        if commit:
            self.save(update_fields=["is_paid", "received_by", "paid_at"])

        return self