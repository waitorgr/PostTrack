from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models import TrackingEvent
from .serializers import TrackingEventSerializer, TrackingEventPublicSerializer
from shipments.models import Shipment


class TrackingEventViewSet(ModelViewSet):
    queryset = TrackingEvent.objects.select_related("shipment", "location").all()
    serializer_class = TrackingEventSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # публічний трекінг — без логіну
        if self.action == "track":
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get"], url_path=r"track/(?P<tracking_code>[^/.]+)")
    def track(self, request, tracking_code=None):
        """
        Публічний перегляд трекінгу за tracking_code.
        Повертає список подій.
        """
        shipment = Shipment.objects.filter(tracking_code=tracking_code).first()
        if not shipment:
            raise NotFound("Shipment not found.")

        events = TrackingEvent.objects.filter(shipment=shipment).select_related("location").order_by("created_at")
        return Response({
            "tracking_code": tracking_code,
            "events": TrackingEventPublicSerializer(events, many=True).data
        })
