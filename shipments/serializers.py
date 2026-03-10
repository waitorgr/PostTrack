from rest_framework import serializers
from locations.models import Location, LocationType
from tracking.models import TrackingEvent
from tracking.serializers import TrackingEventPublicSerializer
from .models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    origin = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(type=LocationType.POST_OFFICE),
        required=False,
        allow_null=True,
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(type=LocationType.POST_OFFICE),
        required=True,
    )

    class Meta:
        model = Shipment
        fields = "__all__"
        read_only_fields = ("tracking_code", "created_at", "updated_at", "created_by", "status")


class ShipmentPublicBriefSerializer(serializers.ModelSerializer):
    origin_code = serializers.CharField(source="origin.code", read_only=True)
    destination_code = serializers.CharField(source="destination.code", read_only=True)

    last_status = serializers.SerializerMethodField()
    last_location_code = serializers.SerializerMethodField()
    last_location_name = serializers.SerializerMethodField()
    last_update_at = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = (
            "tracking_code",
            "status",
            "origin_code",
            "destination_code",
            "last_status",
            "last_location_code",
            "last_location_name",
            "last_update_at",
        )

    def _last_event(self, obj):
        return (
            TrackingEvent.objects.filter(shipment=obj)
            .select_related("location")
            .order_by("-created_at")  # якщо timestamp — заміни на "-timestamp"
            .first()
        )

    def get_last_status(self, obj):
        ev = self._last_event(obj)
        return ev.status if ev else obj.status

    def get_last_location_code(self, obj):
        ev = self._last_event(obj)
        return ev.location.code if ev and ev.location else None

    def get_last_location_name(self, obj):
        ev = self._last_event(obj)
        return ev.location.name if ev and ev.location else None

    def get_last_update_at(self, obj):
        ev = self._last_event(obj)
        return ev.created_at if ev else obj.updated_at  # якщо timestamp — ev.timestamp


class ShipmentPublicTrackingSerializer(serializers.ModelSerializer):
    origin_code = serializers.CharField(source="origin.code", read_only=True)
    destination_code = serializers.CharField(source="destination.code", read_only=True)
    events = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = (
            "tracking_code",
            "status",
            "created_at",
            "origin_code",
            "destination_code",
            "description",
            "events",
        )

    def get_events(self, obj):
        qs = (
            TrackingEvent.objects.filter(shipment=obj)
            .select_related("location")
            .order_by("created_at")  # якщо timestamp — заміни на "timestamp"
        )
        return TrackingEventPublicSerializer(qs, many=True).data
