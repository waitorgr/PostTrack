def create_tracking_event(shipment, event_type, location=None, created_by=None, note='', is_public=True):
    from .models import TrackingEvent
    return TrackingEvent.objects.create(
        shipment=shipment,
        event_type=event_type,
        location=location,
        created_by=created_by,
        note=note,
        is_public=is_public,
        created_at=None,
    )
