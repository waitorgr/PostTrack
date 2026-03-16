from rest_framework import serializers
from .models import Route, RouteStatus


class RouteListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    group_code = serializers.CharField(source='dispatch_group.code', read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'group_code', 'driver_name', 'status', 'status_display',
            'origin_name', 'destination_name', 'is_auto',
            'scheduled_departure', 'created_at',
        ]


class RouteDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    group_code = serializers.CharField(source='dispatch_group.code', read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'driver', 'driver_name',
            'dispatch_group', 'group_code',
            'origin', 'origin_name', 'destination', 'destination_name',
            'status', 'status_display', 'is_auto',
            'scheduled_departure', 'notes', 'created_at',
        ]


class RouteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['driver', 'dispatch_group', 'destination', 'scheduled_departure', 'notes']

    def validate_driver(self, value):
        from accounts.models import Role
        if value.role != Role.DRIVER:
            raise serializers.ValidationError("Вказаний користувач не є водієм.")
        return value

    def create(self, validated_data):
        dispatch_group = validated_data['dispatch_group']
        validated_data['origin'] = dispatch_group.origin
        return super().create(validated_data)


class RouteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['driver', 'scheduled_departure', 'notes']
