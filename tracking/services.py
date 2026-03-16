from .models import TrackingEvent


class TrackingService:

    @staticmethod
    def add_event(shipment, event_type: str, location, performed_by,
                  note: str = "", is_public: bool = True) -> TrackingEvent:
        return TrackingEvent.objects.create(
            shipment=shipment,
            event_type=event_type,
            location=location,
            created_by=performed_by,
            note=note,
            is_public=is_public,
        )

    @staticmethod
    def get_public_history(tracking_number: str) -> dict:
        from shipments.models import Shipment
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
        except Shipment.DoesNotExist:
            return None

        events = TrackingEvent.objects.filter(
            shipment=shipment, is_public=True
        ).select_related("location").order_by("created_at")

        return {
            "tracking_number": tracking_number,
            "status": shipment.status,
            "status_display": shipment.get_status_display(),
            "receiver_name": shipment.receiver_name,
            "origin": shipment.origin.city if shipment.origin else "",
            "destination": shipment.destination.city if shipment.destination else "",
            "events": [
                {
                    "type": e.event_type,
                    "label": e.get_event_type_display(),
                    "location": e.location.name if e.location else "",
                    "city": e.location.city if e.location else "",
                    "time": e.created_at,
                    "note": e.note,
                }
                for e in events
            ],
        }
