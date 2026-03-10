from rest_framework import serializers
from .models import TrackingEvent


class TrackingEventPublicSerializer(serializers.ModelSerializer):
    location_code = serializers.CharField(source="location.code", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = TrackingEvent
        fields = (
            "id",
            "status",
            "created_at",
            "location_code",
            "location_name",
            "comment",
        )
        read_only_fields = fields


class TrackingEventSerializer(serializers.ModelSerializer):
    """
    Для staff (якщо колись треба буде).
    """
    class Meta:
        model = TrackingEvent
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
