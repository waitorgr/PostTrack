from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Route, RouteStep, RouteStatus, RouteStepType


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


class RouteStepSerializer(serializers.ModelSerializer):
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    location_name = serializers.SerializerMethodField()
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = RouteStep
        fields = [
            'id',
            'order',
            'location',
            'location_name',
            'step_type',
            'step_type_display',
            'planned_arrival',
            'planned_departure',
            'actual_arrival',
            'actual_departure',
            'notes',
            'is_completed',
            'created_at',
        ]
        read_only_fields = ['id', 'step_type_display', 'location_name', 'is_completed', 'created_at']

    def get_location_name(self, obj):
        return get_object_display(obj.location, 'name', 'title', 'code')


class RouteBaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    driver_name = serializers.SerializerMethodField()
    origin_name = serializers.SerializerMethodField()
    destination_name = serializers.SerializerMethodField()
    group_code = serializers.CharField(source='dispatch_group.code', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    step_count = serializers.SerializerMethodField()
    is_editable = serializers.BooleanField(read_only=True)

    def get_driver_name(self, obj):
        return get_object_display(obj.driver, 'full_name', 'username', 'email')

    def get_origin_name(self, obj):
        return get_object_display(obj.origin, 'name', 'title', 'code')

    def get_destination_name(self, obj):
        return get_object_display(obj.destination, 'name', 'title', 'code')

    def get_created_by_name(self, obj):
        return get_object_display(obj.created_by, 'full_name', 'username', 'email')

    def get_step_count(self, obj):
        if hasattr(obj, '_step_count'):
            return obj._step_count
        return obj.steps.count()


class RouteListSerializer(RouteBaseSerializer):
    class Meta:
        model = Route
        fields = [
            'id',
            'dispatch_group',
            'group_code',
            'driver',
            'driver_name',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'status',
            'status_display',
            'is_auto',
            'step_count',
            'is_editable',
            'scheduled_departure',
            'created_at',
        ]
        read_only_fields = fields


class RouteDetailSerializer(RouteBaseSerializer):
    steps = RouteStepSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            'id',
            'driver',
            'driver_name',
            'dispatch_group',
            'group_code',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'status',
            'status_display',
            'is_auto',
            'scheduled_departure',
            'notes',
            'created_by',
            'created_by_name',
            'step_count',
            'is_editable',
            'steps',
            'created_at',
        ]
        read_only_fields = fields


class RouteCreateSerializer(RouteBaseSerializer):
    class Meta:
        model = Route
        fields = [
            'id',
            'dispatch_group',
            'group_code',
            'driver',
            'driver_name',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'status',
            'status_display',
            'is_auto',
            'scheduled_departure',
            'notes',
            'created_by',
            'created_by_name',
            'step_count',
            'is_editable',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'group_code',
            'origin',
            'origin_name',
            'destination',
            'destination_name',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'step_count',
            'is_editable',
            'created_at',
        ]
        extra_kwargs = {
            'driver': {'required': False, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True},
        }

    def validate_dispatch_group(self, value):
        if Route.objects.filter(dispatch_group=value).exists():
            raise serializers.ValidationError('Для цієї dispatch-групи маршрут уже існує.')
        return value

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
        dispatch_group = attrs.get('dispatch_group')
        driver = attrs.get('driver')
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not dispatch_group:
            raise serializers.ValidationError({
                'dispatch_group': 'Потрібно вказати dispatch-групу.'
            })

        candidate = Route(
            dispatch_group=dispatch_group,
            origin=dispatch_group.origin,
            destination=dispatch_group.destination,
            driver=driver or getattr(dispatch_group, 'driver', None),
            scheduled_departure=attrs.get('scheduled_departure'),
            notes=attrs.get('notes', ''),
            is_auto=attrs.get('is_auto', False),
            created_by=user,
            status=RouteStatus.DRAFT,
        )

        try:
            candidate.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, 'message_dict'):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({'non_field_errors': exc.messages})

        return attrs

    def create(self, validated_data):
        dispatch_group = validated_data.pop('dispatch_group')
        driver = validated_data.pop('driver', None) or getattr(dispatch_group, 'driver', None)
    
        request = self.context.get('request')
        user = getattr(request, 'user', None)
    
        return Route.objects.create(
            dispatch_group=dispatch_group,
            origin=dispatch_group.origin,
            destination=dispatch_group.destination,
            driver=driver,
            created_by=user,
            **validated_data,
        )


class RouteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['driver', 'scheduled_departure', 'notes']

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
        instance = self.instance

        if instance and not instance.is_editable:
            raise serializers.ValidationError({
                'detail': 'Маршрут можна редагувати лише у статусі "Чернетка" або "Підтверджено".'
            })

        candidate = Route(
            id=instance.id,
            dispatch_group=instance.dispatch_group,
            origin=instance.origin,
            destination=instance.destination,
            driver=attrs.get('driver', instance.driver),
            scheduled_departure=attrs.get('scheduled_departure', instance.scheduled_departure),
            notes=attrs.get('notes', instance.notes),
            is_auto=instance.is_auto,
            created_by=instance.created_by,
            status=instance.status,
        )

        try:
            candidate.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, 'message_dict'):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({'non_field_errors': exc.messages})

        return attrs