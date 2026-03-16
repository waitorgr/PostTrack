from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'type', 'type_display', 'city', 'address', 'code', 'is_active']
