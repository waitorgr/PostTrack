from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role
from django.core.exceptions import ValidationError as DjangoValidationError


class UserMeSerializer(serializers.ModelSerializer):
    """Поточний авторизований користувач."""
    location_name = serializers.CharField(source='location.name', read_only=True, default=None)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'patronymic',
            'email', 'phone', 'role',
            'location', 'location_name',
            'region', 'region_name',
        ]
        read_only_fields = [
            'id', 'username', 'role',
            'location', 'location_name',
            'region', 'region_name',
        ]


class CustomerRegisterSerializer(serializers.ModelSerializer):
    """Самостійна реєстрація клієнта."""
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'patronymic',
            'email', 'phone', 'password',
        ]

    def validate_phone(self, value):
        if not value.startswith('+380') or len(value) != 13:
            raise serializers.ValidationError("Формат телефону: +380XXXXXXXXX")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data, role=Role.CUSTOMER)
        user.set_password(password)
        user.save()
        return user


class WorkerRegisterSerializer(serializers.ModelSerializer):
    """HR реєструє працівника."""
    password = serializers.CharField(
        write_only=True,
        default='adminadmin',
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'patronymic',
            'email', 'phone', 'role', 'location','region', 'password',
        ]

    def validate_role(self, value):
        forbidden = (Role.CUSTOMER, Role.ADMIN)
        if value in forbidden:
            raise serializers.ValidationError("HR може реєструвати лише працівників.")
        return value
    def validate(self, attrs):
        user = User(**attrs)
        try:
            user.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', 'adminadmin')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class WorkerListSerializer(serializers.ModelSerializer):
    """Список працівників для HR."""
    location_name = serializers.CharField(source='location.name', read_only=True, default=None)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'patronymic',
            'email', 'phone', 'role', 'role_display',
            'location', 'location_name',
            'region', 'region_name',
            'is_active', 'date_joined',
        ]


class WorkerUpdateSerializer(serializers.ModelSerializer):
    """HR оновлює дані працівника."""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'patronymic',
            'email', 'phone', 'role', 'location', 'region', 'is_active',
        ]

    def validate_role(self, value):
        if value in (Role.CUSTOMER, Role.ADMIN):
            raise serializers.ValidationError("Недопустима роль.")
        return value
    
    def validate(self, attrs):
        user = User(**attrs)
        try:
            user.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
        return attrs
