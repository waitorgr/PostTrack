from django.db import models
from core.models import TimeStampedModel
from locations.models import Location
from shipments.models import Shipment, ShipmentStatus


class TrackingEvent(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=64, choices=ShipmentStatus.choices)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="tracking_events", null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.shipment.tracking_code} -> {self.status}"
