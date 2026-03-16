from rest_framework import serializers
from .models import DispatchGroup, DispatchGroupItem
from shipments.serializers import ShipmentListSerializer


class DispatchGroupItemSerializer(serializers.ModelSerializer):
    shipment_detail = ShipmentListSerializer(source='shipment', read_only=True)

    class Meta:
        model = DispatchGroupItem
        fields = ['id', 'shipment', 'shipment_detail', 'added_at']


class DispatchGroupListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True, default=None)
    shipment_count = serializers.SerializerMethodField()

    class Meta:
        model = DispatchGroup
        fields = [
            'id', 'code', 'status', 'status_display',
            'origin_name', 'destination_name', 'driver_name',
            'shipment_count', 'departed_at', 'arrived_at', 'created_at',
        ]

    def get_shipment_count(self, obj):
        return obj.items.count()


class DispatchGroupDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default=None)
    items = DispatchGroupItemSerializer(many=True, read_only=True)

    class Meta:
        model = DispatchGroup
        fields = [
            'id', 'code', 'status', 'status_display',
            'origin', 'origin_name', 'destination', 'destination_name',
            'driver', 'driver_name', 'created_by_name',
            'items', 'departed_at', 'arrived_at', 'created_at',
        ]


class DispatchGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchGroup
        fields = ['destination', 'driver']

    def validate_driver(self, value):
        from accounts.models import Role
        if value and value.role != Role.DRIVER:
            raise serializers.ValidationError("Вказаний користувач не є водієм.")
        return value


class AddShipmentSerializer(serializers.Serializer):
    tracking_number = serializers.CharField()

    def validate_tracking_number(self, value):
        from shipments.models import Shipment
        try:
            return Shipment.objects.get(tracking_number=value)
        except Shipment.DoesNotExist:
            raise serializers.ValidationError("Посилку з таким номером не знайдено.")
