from rest_framework import serializers

from locations.models import LocationType
from .models import Payment, Shipment, ShipmentStatus


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


class ShipmentListSerializer(serializers.ModelSerializer):
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
            "weight",
            "price",
            "status",
            "status_display",
            "payment_type",
            "payment_type_display",
            "created_at",
        ]
        read_only_fields = fields


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """
    Працівник пошти створює посилку.
    origin і created_by підставляються з view.
    price і tracking_number формуються моделлю/сервісом.
    """
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


class ShipmentDetailSerializer(serializers.ModelSerializer):
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
            "weight",
            "description",
            "price",
            "payment_type",
            "payment_type_display",
            "status",
            "status_display",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "payment",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        return getattr(obj.created_by, "full_name", str(obj.created_by))


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