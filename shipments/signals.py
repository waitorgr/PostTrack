from django.db.models.signals import post_save
from django.dispatch import receiver

from shipments.models import Shipment, ShipmentStatus
from tracking.models import TrackingEvent
from tracking.utils import create_tracking_event


@receiver(post_save, sender=Shipment, dispatch_uid="shipments_create_initial_tracking")
def create_initial_tracking(sender, instance: Shipment, created: bool, **kwargs):
    if not created:
        return

    if TrackingEvent.objects.filter(
        shipment=instance,
        event_type=ShipmentStatus.ACCEPTED,
    ).exists():
        return

    create_tracking_event(
        shipment=instance,
        event_type=ShipmentStatus.ACCEPTED,
        location=instance.origin,
        created_by=instance.created_by,
        note="Посилку прийнято та зареєстровано у системі.",
        is_public=True,
    )