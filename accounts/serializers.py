from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Role, User


class UserValidationMixin:
    def validate_email(self, value):
        value = (value or "").strip().lower()
        if not value:
            raise serializers.ValidationError("Email є обов’язковим.")

        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Користувач з таким email вже існує.")

        return value

    def validate_phone(self, value):
        value = (value or "").strip()

        if not value.startswith("+380") or len(value) != 13 or not value[1:].isdigit():
            raise serializers.ValidationError("Формат телефону: +380XXXXXXXXX")

        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Користувач з таким телефоном вже існує.")

        return value

    def _build_candidate_user(self, attrs):
        if not self.instance:
            return User(**attrs)

        instance = self.instance

        candidate = User(
            username=attrs.get("username", instance.username),
            first_name=attrs.get("first_name", instance.first_name),
            last_name=attrs.get("last_name", instance.last_name),
            patronymic=attrs.get("patronymic", instance.patronymic),
            email=attrs.get("email", instance.email),
            phone=attrs.get("phone", instance.phone),
            role=attrs.get("role", instance.role),
            location=attrs.get("location", instance.location),
            region=attrs.get("region", instance.region),
            is_active=attrs.get("is_active", instance.is_active),
            is_staff=instance.is_staff,
            is_superuser=instance.is_superuser,
        )
        candidate.pk = instance.pk
        candidate.password = instance.password
        candidate.last_login = instance.last_login
        candidate.date_joined = instance.date_joined
        return candidate

    def validate(self, attrs):
        candidate = self._build_candidate_user(attrs)
        try:
            candidate.clean()
        except DjangoValidationError as e:
            if hasattr(e, "message_dict"):
                raise serializers.ValidationError(e.message_dict)
            raise serializers.ValidationError(e.messages)
        return attrs


class UserMeSerializer(UserValidationMixin, serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name", read_only=True, default=None)
    region_name = serializers.CharField(source="region.name", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone",
            "role",
            "location",
            "location_name",
            "region",
            "region_name",
        ]
        read_only_fields = [
            "id",
            "username",
            "role",
            "location",
            "location_name",
            "region",
            "region_name",
        ]


class CustomerRegisterSerializer(UserValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone",
            "password",
        ]
        extra_kwargs = {
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "patronymic": {"required": True},
            "email": {"required": True},
            "phone": {"required": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=Role.CUSTOMER)
        user.set_password(password)
        user.save()
        return user


class WorkerRegisterSerializer(UserValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone",
            "role",
            "location",
            "region",
            "password",
        ]
        extra_kwargs = {
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "patronymic": {"required": True},
            "email": {"required": True},
            "phone": {"required": True},
            "role": {"required": True},
            "password": {"required": True},
        }

    def validate_role(self, value):
        if value in (Role.CUSTOMER, Role.ADMIN):
            raise serializers.ValidationError("HR може реєструвати лише працівників.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class WorkerListSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name", read_only=True, default=None)
    region_name = serializers.CharField(source="region.name", read_only=True, default=None)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone",
            "role",
            "role_display",
            "location",
            "location_name",
            "region",
            "region_name",
            "is_active",
            "date_joined",
        ]


class WorkerUpdateSerializer(UserValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone",
            "role",
            "location",
            "region",
            "is_active",
        ]

    def validate_role(self, value):
        if value in (Role.CUSTOMER, Role.ADMIN):
            raise serializers.ValidationError("Недопустима роль.")
        return value
    

class DriverOptionSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name().strip() or obj.username