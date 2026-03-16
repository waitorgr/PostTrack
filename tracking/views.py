from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from django.shortcuts import get_object_or_404

from shipments.models import Shipment
from .models import TrackingEvent
from .serializers import TrackingEventSerializer, PublicTrackingSerializer


class PublicTrackingView(APIView):
    """GET /api/tracking/public/<tracking_number>/ — без авторизації."""
    permission_classes = [AllowAny]

    def get(self, request, tracking_number):
        shipment = get_object_or_404(Shipment, tracking_number=tracking_number)
        events = shipment.events.filter(is_public=True).select_related('location')
        data = {
            'tracking_number': shipment.tracking_number,
            'status': shipment.status,
            'status_display': shipment.get_status_display(),
            'origin_city': shipment.origin.city,
            'destination_city': shipment.destination.city,
            'sender_name': f"{shipment.sender_last_name} {shipment.sender_first_name[0]}.",
            'receiver_name': f"{shipment.receiver_last_name} {shipment.receiver_first_name[0]}.",
            'created_at': shipment.created_at,
            'events': TrackingEventSerializer(events, many=True).data,
        }
        return Response(data)


class ShipmentEventsView(generics.ListAPIView):
    """GET /api/tracking/events/?shipment=<id> — всі події посилки (для авторизованих)."""
    permission_classes = [IsAuthenticated]
    serializer_class = TrackingEventSerializer

    def get_queryset(self):
        shipment_id = self.request.query_params.get('shipment')
        if not shipment_id:
            return TrackingEvent.objects.none()
        return TrackingEvent.objects.filter(
            shipment_id=shipment_id
        ).select_related('location', 'created_by').order_by('-created_at')
