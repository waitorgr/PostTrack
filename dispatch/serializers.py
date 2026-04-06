from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus
from shipments.models import Shipment
from shipments.serializers import ShipmentListSerializer
from locations.models import Location


def get_object_display(obj, *attrs):
    if obj is None:
        return None

    for attr in attrs:
        value = getattr(obj, attr, None)
        if callable(value):
            try:
                value = value()
            except TypeError:
                value = None
        if value not in (None, ''):
            return value

    return str(obj)


class DispatchGroupItemSerializer(serializers.ModelSerializer):
    shipment_detail = ShipmentListSerializer(source='shipment', read_only=True)
    shipment_tracking_number = serializers.SerializerMethodField()
    added_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DispatchGroupItem
        fields = [
            'id',
            'shipment',
            'shipment_tracking_number',
            'shipment_detail',
            'added_by',
            'added_by_name',
            'added_at',
        ]
        read_only_fields = ['id', 'added_at', 'shipment_detail', 'shipment_tracking_number', 'added_by_name']

    def get_shipment_tracking_number(self, obj):
        return getattr(obj.shipment, 'tracking_number', None)

    def get_added_by_name(self, obj):
        return get_object_display(obj.added_by, 'full_name', 'username', 'email')


class DispatchGroupBaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_name = serializers.SerializerMethodField()
    destination_name = serializers.SerializerMethodField()
    current_location_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    shipment_count = serializers.SerializerMethodField()
    is_editable = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    def get_origin_name(self, obj):
        return get_object_display(obj.origin, 'name', 'title', 'code')

    def get_destination_name(self, obj):
        return get_object_display(obj.destination, 'name', 'title', 'code')

    def get_current_location_name(self, obj):
        return get_object_display(obj.current_location, 'name', 'title', 'code')

    def get_driver_name(self, obj):
        return get_object_display(obj.driver, 'full_name', 'username', 'email')

    def get_created_by_name(self, obj):
        return get_object_display(obj.created_by, 'full_name', 'username', 'email')

    def get_shipment_count(self, obj):
        if hasattr(obj, '_items_count'):
            return obj._items_count
        if hasattr(obj, 'items_count'):
            return obj.items_count
        return obj.items.count()


class DispatchGroupListSerializer(DispatchGroupBaseSerializer):
    class Meta:
        model = DispatchGroup
        fields = [
            'id',
            'code',
            'status',
            'status_display',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'current_location',
            'current_location_name',
            'driver',
            'driver_name',
            'shipment_count',
            'is_editable',
            'is_active',
            'departed_at',
            'arrived_at',
            'created_at',
        ]
        read_only_fields = fields


class DispatchGroupDetailSerializer(DispatchGroupBaseSerializer):
    items = DispatchGroupItemSerializer(many=True, read_only=True)

    class Meta:
        model = DispatchGroup
        fields = [
            'id',
            'code',
            'status',
            'status_display',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'current_location',
            'current_location_name',
            'driver',
            'driver_name',
            'created_by',
            'created_by_name',
            'shipment_count',
            'is_editable',
            'is_active',
            'items',
            'departed_at',
            'arrived_at',
            'created_at',
        ]
        read_only_fields = fields


class DispatchGroupCreateSerializer(DispatchGroupBaseSerializer):
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_active=True)
    )

    class Meta:
        model = DispatchGroup
        fields = [
            'id',
            'code',
            'status',
            'status_display',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'current_location',
            'current_location_name',
            'driver',
            'driver_name',
            'created_by',
            'created_by_name',
            'shipment_count',
            'is_editable',
            'is_active',
            'departed_at',
            'arrived_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'code',
            'status',
            'status_display',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'current_location',
            'current_location_name',
            'created_by',
            'created_by_name',
            'shipment_count',
            'is_editable',
            'is_active',
            'departed_at',
            'arrived_at',
            'created_at',
        ]
        extra_kwargs = {
            'driver': {'required': False, 'allow_null': True},
        }

    def validate_driver(self, value):
        if not value:
            return value

        try:
            from accounts.models import Role
            if value.role != getattr(Role, 'DRIVER', 'driver'):
                raise serializers.ValidationError('Вказаний користувач не є водієм.')
        except ImportError:
            pass

        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        origin = getattr(user, 'location', None)
        destination = attrs.get('destination')

        if origin is None:
            raise serializers.ValidationError({
                'origin': 'У користувача немає прив’язаної локації.'
            })

        if destination is None:
            raise serializers.ValidationError({
                'destination': 'Потрібно вказати destination.'
            })

        if origin.id == destination.id:
            raise serializers.ValidationError({
                'destination': 'Destination не може збігатися з origin.'
            })

        candidate = DispatchGroup(
            origin=origin,
            destination=destination,
            driver=attrs.get('driver'),
            current_location=origin,
            created_by=user,
            status=DispatchGroupStatus.FORMING,
        )

        try:
            candidate.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, 'message_dict'):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({'non_field_errors': exc.messages})

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        origin = user.location
        destination = validated_data.pop('destination')

        group = DispatchGroup.objects.create(
            origin=origin,
            destination=destination,
            current_location=origin,
            created_by=user,
            **validated_data,
        )
        return group


class AddShipmentSerializer(serializers.Serializer):
    tracking_number = serializers.CharField()

    def validate(self, attrs):
        tracking_number = attrs.get('tracking_number')

        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
        except Shipment.DoesNotExist:
            raise serializers.ValidationError({
                'tracking_number': 'Посилку не знайдено'
            })

        attrs['shipment'] = shipment
        return attrs