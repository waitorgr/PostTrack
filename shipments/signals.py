from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from shipments.models import Shipment, ShipmentStatus
from tracking.models import TrackingEvent


@receiver(post_save, sender=Shipment)
def create_initial_tracking(sender, instance: Shipment, created: bool, **kwargs):
    if not created:
        return

    with transaction.atomic():
        
        if instance.status != ShipmentStatus.ACCEPTED:
            TrackingEvent.objects.create(
                shipment=instance,
                status=instance.status,
                location=instance.origin,
                comment="Shipment created."
            )
            return

        
        Shipment.objects.filter(pk=instance.pk).update(status=ShipmentStatus.ACCEPTED)

        TrackingEvent.objects.create(
            shipment=instance,
            status=ShipmentStatus.AT_POST_OFFICE,
            location=instance.origin,
            comment="Registered at origin post office."
        )
