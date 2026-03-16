from rest_framework import serializers
from .models import Shipment, Payment, ShipmentStatus


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(source='received_by.full_name', read_only=True, default=None)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'is_paid', 'paid_at', 'received_by', 'received_by_name']
        read_only_fields = ['id', 'paid_at', 'received_by_name']


class ShipmentListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number',
            'sender_full_name', 'receiver_full_name',
            'origin_name', 'destination_name',
            'weight', 'price', 'status', 'status_display',
            'payment_type', 'created_at',
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Працівник пошти створює посилку. origin береться автоматично."""
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'sender_first_name', 'sender_last_name', 'sender_patronymic',
            'sender_phone', 'sender_email',
            'receiver_first_name', 'receiver_last_name', 'receiver_patronymic',
            'receiver_phone', 'receiver_email',
            'destination', 'weight', 'description', 'payment_type', 'price',
        ]

    def validate_destination(self, value):
        from locations.models import LocationType
        if value.type not in (LocationType.POST_OFFICE,):
            raise serializers.ValidationError("Призначення має бути поштовим відділенням.")
        return value

    def create(self, validated_data):
        weight = validated_data.get('weight')
        validated_data['price'] = Shipment.calculate_price(weight)
        return super().create(validated_data)


class ShipmentDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    origin_city = serializers.CharField(source='origin.city', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    destination_city = serializers.CharField(source='destination.city', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default=None)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number',
            'sender_first_name', 'sender_last_name', 'sender_patronymic',
            'sender_phone', 'sender_email', 'sender_full_name',
            'receiver_first_name', 'receiver_last_name', 'receiver_patronymic',
            'receiver_phone', 'receiver_email', 'receiver_full_name',
            'origin', 'origin_name', 'origin_city',
            'destination', 'destination_name', 'destination_city',
            'weight', 'description', 'price',
            'payment_type', 'payment_type_display',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'payment',
        ]
        read_only_fields = fields


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ShipmentStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True)


class PaymentConfirmSerializer(serializers.Serializer):
    """Підтвердження оплати після доставки."""
    pass
