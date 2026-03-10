from rest_framework import serializers

from shipments.models import Shipment, ShipmentStatus
from locations.models import Location, LocationType

from .models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus


class DispatchGroupItemSerializer(serializers.ModelSerializer):
    shipment_tracking_code = serializers.CharField(source="shipment.tracking_code", read_only=True)

    class Meta:
        model = DispatchGroupItem
        fields = ("id", "shipment", "shipment_tracking_code", "created_at")


class DispatchGroupSerializer(serializers.ModelSerializer):
    items = DispatchGroupItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = DispatchGroup
        fields = "__all__"
        read_only_fields = (
            "id",
            "group_code",
            "created_at",
            "updated_at",

            # системні поля — не даємо міняти вручну
            "status",
            "created_by",
            "from_location",
            "to_location",

            # підтвердження
            "pickup_driver", "pickup_employee", "pickup_at",
            "dropoff_driver", "dropoff_employee", "dropoff_at",
        )


class DispatchGroupCreateSerializer(serializers.ModelSerializer):
    shipment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        required=False,
        allow_empty=False,   # якщо поле передали — список не може бути пустим
    )
    to_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DispatchGroup
        fields = ("to_location", "shipment_ids")  # from_location/created_by ставимо у view

    def validate_shipment_ids(self, value):
        """
        1) унікалізація ids
        2) перевірка існування shipment
        3) перевірка що shipment не в активній групі
        4) опціонально: перевірка статусів для відправки з вузла працівника
        """
        ids = list(dict.fromkeys(value))  # прибираємо дублікати, зберігаємо порядок

        # 1) існування
        existing = set(Shipment.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = [sid for sid in ids if sid not in existing]
        if missing:
            raise serializers.ValidationError(f"Shipments not found: {missing[:10]}")

        # 2) не в активній групі (дозволяємо тільки якщо попередня група OPENED/CANCELED)
        active_statuses = {
            DispatchGroupStatus.CREATED,
            DispatchGroupStatus.SEALED,
            DispatchGroupStatus.IN_TRANSIT,
            DispatchGroupStatus.DROPPED_OFF,
        }
        already_used = (
            DispatchGroupItem.objects
            .filter(shipment_id__in=ids, group__status__in=active_statuses)
            .values_list("shipment_id", flat=True)
            .distinct()
        )
        already_used = set(already_used)
        if already_used:
            raise serializers.ValidationError(
                f"Some shipments already belong to an active group: {sorted(list(already_used))[:10]}"
            )

        # 3) (опційно) перевірка статусу посилок відповідно до вузла працівника (from_location)
        # from_location у нас береться з request.user.assigned_location у view,
        # тому тут можемо дістати його через context.
        req = self.context.get("request")
        user_loc = getattr(getattr(req, "user", None), "assigned_location", None)

        if user_loc:
            if user_loc.type == LocationType.POST_OFFICE:
                allowed = {ShipmentStatus.AT_POST_OFFICE}
            elif user_loc.type == LocationType.SORTING_CITY:
                allowed = {ShipmentStatus.SORTED_WAITING_FOR_DISPATCH}
            elif user_loc.type == LocationType.DISTRIBUTION_CENTER:
                allowed = {ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE}
            else:
                allowed = None

            if allowed is not None:
                bad = list(
                    Shipment.objects
                    .filter(id__in=ids)
                    .exclude(status__in=allowed)
                    .values_list("tracking_code", "status")[:5]
                )
                if bad:
                    sample = ", ".join([f"{code}:{st}" for code, st in bad])
                    raise serializers.ValidationError(
                        f"Some shipments have invalid status for grouping from this location: {sample}"
                    )

        return ids

    def create(self, validated_data):
        shipment_ids = validated_data.pop("shipment_ids", [])

        group = DispatchGroup.objects.create(**validated_data)

        if shipment_ids:
            DispatchGroupItem.objects.bulk_create(
                [DispatchGroupItem(group=group, shipment_id=sid) for sid in shipment_ids]
            )

        return group
