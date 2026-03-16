from rest_framework import serializers
from .models import TrackingEvent


class TrackingEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True, default=None)
    location_city = serializers.CharField(source='location.city', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default=None)

    class Meta:
        model = TrackingEvent
        fields = [
            'id', 'event_type', 'event_type_display',
            'location', 'location_name', 'location_city',
            'note', 'is_public', 'created_by_name', 'created_at',
        ]


class PublicTrackingSerializer(serializers.Serializer):
    """Публічний трекінг — без конфіденційної інформації."""
    tracking_number = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    origin_city = serializers.CharField()
    destination_city = serializers.CharField()
    sender_name = serializers.CharField()
    receiver_name = serializers.CharField()
    created_at = serializers.DateTimeField()
    events = TrackingEventSerializer(many=True)
