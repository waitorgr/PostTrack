from rest_framework import serializers

from locations.models import LocationType
from .models import Payment, Shipment, ShipmentRouteStep, ShipmentStatus
from tracking.models import TrackingEvent


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "is_paid",
            "paid_at",
            "received_by",
            "received_by_name",
        ]
        read_only_fields = fields

    def get_received_by_name(self, obj):
        if not obj.received_by:
            return None
        return getattr(obj.received_by, "full_name", str(obj.received_by))


class ShipmentRouteStepSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name", read_only=True)
    location_type = serializers.CharField(source="location.type", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ShipmentRouteStep
        fields = [
            "id",
            "order",
            "location",
            "location_name",
            "location_type",
            "location_code",
            "status",
            "status_display",
            "actual_arrival_at",
            "actual_departure_at",
        ]
        read_only_fields = fields


class ShipmentRoutingMixin(serializers.Serializer):
    current_location_id = serializers.SerializerMethodField()
    current_location_name = serializers.SerializerMethodField()
    current_location_type = serializers.SerializerMethodField()
    current_location_code = serializers.SerializerMethodField()

    next_hop_id = serializers.SerializerMethodField()
    next_hop_name = serializers.SerializerMethodField()
    next_hop_type = serializers.SerializerMethodField()
    next_hop_code = serializers.SerializerMethodField()

    def _get_current_location(self, obj):
        active_step = getattr(obj, "active_route_step", None)
        if active_step is not None and getattr(active_step, "location", None) is not None:
            return active_step.location
        return getattr(obj, "current_location", None)

    def _get_next_hop(self, obj):
        next_step = getattr(obj, "next_route_step", None)
        if next_step is not None:
            return getattr(next_step, "location", None)
        return None

    def get_current_location_id(self, obj):
        location = self._get_current_location(obj)
        return getattr(location, "id", None)

    def get_current_location_name(self, obj):
        location = self._get_current_location(obj)
        return getattr(location, "name", None)

    def get_current_location_type(self, obj):
        location = self._get_current_location(obj)
        return getattr(location, "type", None)

    def get_current_location_code(self, obj):
        location = self._get_current_location(obj)
        return getattr(location, "code", None)

    def get_next_hop_id(self, obj):
        next_hop = self._get_next_hop(obj)
        return getattr(next_hop, "id", None)

    def get_next_hop_name(self, obj):
        next_hop = self._get_next_hop(obj)
        return getattr(next_hop, "name", None)

    def get_next_hop_type(self, obj):
        next_hop = self._get_next_hop(obj)
        return getattr(next_hop, "type", None)

    def get_next_hop_code(self, obj):
        next_hop = self._get_next_hop(obj)
        return getattr(next_hop, "code", None)


class ShipmentListSerializer(ShipmentRoutingMixin, serializers.ModelSerializer):
    sender_full_name = serializers.CharField(read_only=True)
    receiver_full_name = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_type_display = serializers.CharField(source="get_payment_type_display", read_only=True)
    origin_name = serializers.CharField(source="origin.name", read_only=True)
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "tracking_number",
            "sender_full_name",
            "receiver_full_name",
            "origin_name",
            "destination_name",
            "current_location_id",
            "current_location_name",
            "current_location_type",
            "current_location_code",
            "weight",
            "price",
            "status",
            "status_display",
            "payment_type",
            "payment_type_display",
            "next_hop_id",
            "next_hop_name",
            "next_hop_type",
            "next_hop_code",
            "created_at",
        ]
        read_only_fields = fields


class ShipmentCreateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tracking_number = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "tracking_number",
            "sender_first_name",
            "sender_last_name",
            "sender_patronymic",
            "sender_phone",
            "sender_email",
            "receiver_first_name",
            "receiver_last_name",
            "receiver_patronymic",
            "receiver_phone",
            "receiver_email",
            "destination",
            "weight",
            "description",
            "payment_type",
            "price",
            "status",
        ]
        read_only_fields = ["tracking_number", "price", "status"]

    def validate_destination(self, value):
        if value.type != LocationType.POST_OFFICE:
            raise serializers.ValidationError("Призначення має бути поштовим відділенням.")
        return value

    def validate_weight(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Вага повинна бути більшою за 0.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        user_location = getattr(user, "location", None)
        destination = attrs.get("destination")

        if user_location and destination and user_location.id == destination.id:
            raise serializers.ValidationError({
                "destination": "Відділення призначення має відрізнятися від відділення відправлення."
            })

        return attrs


class ShipmentDetailSerializer(ShipmentRoutingMixin, serializers.ModelSerializer):
    sender_full_name = serializers.CharField(read_only=True)
    receiver_full_name = serializers.CharField(read_only=True)

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_type_display = serializers.CharField(source="get_payment_type_display", read_only=True)

    origin_name = serializers.CharField(source="origin.name", read_only=True)
    origin_city = serializers.CharField(source="origin.city", read_only=True)

    destination_name = serializers.CharField(source="destination.name", read_only=True)
    destination_city = serializers.CharField(source="destination.city", read_only=True)

    created_by_name = serializers.SerializerMethodField()
    payment = PaymentSerializer(read_only=True)
    route_steps = ShipmentRouteStepSerializer(many=True, read_only=True)
    tracking_events = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = [
            "id",
            "tracking_number",
            "sender_first_name",
            "sender_last_name",
            "sender_patronymic",
            "sender_phone",
            "sender_email",
            "sender_full_name",
            "receiver_first_name",
            "receiver_last_name",
            "receiver_patronymic",
            "receiver_phone",
            "receiver_email",
            "receiver_full_name",
            "origin",
            "origin_name",
            "origin_city",
            "destination",
            "destination_name",
            "destination_city",
            "current_location_id",
            "current_location_name",
            "current_location_type",
            "current_location_code",
            "weight",
            "description",
            "price",
            "payment_type",
            "payment_type_display",
            "status",
            "status_display",
            "next_hop_id",
            "next_hop_name",
            "next_hop_type",
            "next_hop_code",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "payment",
            "route_steps",
            "tracking_events",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        return getattr(obj.created_by, "full_name", str(obj.created_by))

    def get_tracking_events(self, obj):
        request = self.context.get("request")
        is_public_request = not getattr(getattr(request, "user", None), "is_authenticated", False)

        qs = TrackingEvent.objects.filter(shipment=obj)

        if is_public_request:
            qs = qs.filter(is_public=True)

        qs = qs.select_related("location", "created_by").order_by("created_at")

        result = []
        for event in qs:
            result.append({
                "id": event.id,
                "event_type": getattr(event, "event_type", None),
                "event_type_label": event.get_event_type_display() if hasattr(event, "get_event_type_display") else getattr(event, "event_type", None),
                "status": getattr(event, "event_type", None),
                "created_at": getattr(event, "created_at", None),
                "note": getattr(event, "note", ""),
                "location": {
                    "id": getattr(event, "location_id", None),
                    "name": getattr(getattr(event, "location", None), "name", None),
                    "code": getattr(getattr(event, "location", None), "code", None),
                },
                "created_by": {
                    "id": getattr(event, "created_by_id", None),
                    "username": getattr(getattr(event, "created_by", None), "username", None),
                },
            })
        return result


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ShipmentStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_note(self, value):
        return value.strip()


class ShipmentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_reason(self, value):
        return value.strip()


class ShipmentReturnSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_reason(self, value):
        return value.strip()


class PaymentConfirmSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_note(self, value):
        return value.strip()
