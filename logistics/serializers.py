from rest_framework import serializers
from .models import Truck, RoutePlan, RouteStop, Trip, TripDispatchGroup


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = "__all__"


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = "__all__"


class RoutePlanSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = RoutePlan
        fields = "__all__"
        read_only_fields = ("created_by",)


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"


class TripDispatchGroupSerializer(serializers.ModelSerializer):
    sequence_number = serializers.IntegerField(required=False)

    class Meta:
        model = TripDispatchGroup
        fields = "__all__"
