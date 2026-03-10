from decimal import Decimal
from django.conf import settings
from django.db import models
from core.models import TimeStampedModel
from core.utils import generate_tracking_code
from locations.models import Location, LocationType



class ParcelSize(models.TextChoices):
    LETTER = "letter", "Letter"
    BIG_LETTER = "big_letter", "Big letter"
    S = "s", "S"
    M = "m", "M"
    L = "l", "L"
    XL = "xl", "XL"
    XXL = "xxl", "XXL"


SIZE_BASE = {
    ParcelSize.LETTER: {"weight_kg": Decimal("0.2"), "price": Decimal("35.00")},
    ParcelSize.BIG_LETTER: {"weight_kg": Decimal("0.5"), "price": Decimal("55.00")},
    ParcelSize.S: {"weight_kg": Decimal("1.0"), "price": Decimal("75.00")},
    ParcelSize.M: {"weight_kg": Decimal("3.0"), "price": Decimal("105.00")},
    ParcelSize.L: {"weight_kg": Decimal("5.0"), "price": Decimal("135.00")},
    ParcelSize.XL: {"weight_kg": Decimal("10.0"), "price": Decimal("175.00")},
    ParcelSize.XXL: {"weight_kg": Decimal("20.0"), "price": Decimal("240.00")},
}


class ShipmentStatus(models.TextChoices):
    CREATED = "created", "Created"

    AT_POST_OFFICE = "at_post_office", "At post office"
    IN_TRANSIT_TO_SORTING_CITY = "in_transit_to_sorting_city", "In transit to sorting city"
    AT_SORTING_CITY = "at_sorting_city", "At sorting city"
    SORTED_WAITING_FOR_DISPATCH = "sorted_waiting_for_dispatch", "Sorted, waiting for dispatch"

    IN_TRANSIT_TO_DISTRIBUTION_CENTER = "in_transit_to_distribution_center", "In transit to distribution center"
    AT_DISTRIBUTION_CENTER = "at_distribution_center", "At distribution center"

    SORTED_WAITING_FOR_POST_OFFICE = "sorted_waiting_for_post_office", "Sorted, waiting for post office"
    IN_TRANSIT_TO_POST_OFFICE = "in_transit_to_post_office", "In transit to post office"

    READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"




class Shipment(TimeStampedModel):
    tracking_code = models.CharField(max_length=32, unique=True, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_shipments",
    )

    # Дані відправника/отримувача (можна буде винести в окремі сутності пізніше)
    sender_name = models.CharField(max_length=120)
    sender_phone = models.CharField(max_length=32)
    recipient_name = models.CharField(max_length=120)
    recipient_phone = models.CharField(max_length=32)

    origin = models.ForeignKey(
    Location,
    on_delete=models.PROTECT,
    related_name="origin_shipments",
    limit_choices_to={"type": LocationType.POST_OFFICE},
    )
    destination = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="destination_shipments",
        limit_choices_to={"type": LocationType.POST_OFFICE},
    )


    size = models.CharField(max_length=16, choices=ParcelSize.choices)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(max_length=64, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED)

    description = models.CharField(max_length=255, blank=True)

    def apply_size_defaults(self):
        base = SIZE_BASE.get(self.size)
        if base:
            self.weight_kg = base["weight_kg"]
            self.price = base["price"]

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            # генеруємо унікальний код
            code = generate_tracking_code()
            while Shipment.objects.filter(tracking_code=code).exists():
                code = generate_tracking_code()
            self.tracking_code = code

        if self.size and (self.weight_kg == Decimal("0.00") or self.price == Decimal("0.00")):
            self.apply_size_defaults()

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.tracking_code} ({self.status})"
