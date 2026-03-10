from django.utils import timezone
from django.db import transaction

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import UserRole
from locations.models import LocationType
from logistics.models import TripStatus, TripDispatchGroup

from shipments.models import Shipment, ShipmentStatus
from dispatch.models import DispatchGroupItem

from .models import DispatchGroup, DispatchGroupStatus
from .serializers import DispatchGroupSerializer, DispatchGroupCreateSerializer


def urole(user):
    return getattr(user, "role", "customer")


def _require_assigned_location(user):
    loc = getattr(user, "assigned_location", None)
    if not loc:
        raise ValidationError("User has no assigned_location.")
    return loc


def _get_trip_link(group: DispatchGroup):
    return getattr(group, "trip_link", None)


def _ensure_driver_can_act_on_group(user, group: DispatchGroup):
    link = _get_trip_link(group)
    if not link:
        raise ValidationError("Group is not assigned to any trip.")

    trip = link.trip

    if trip.status != TripStatus.IN_PROGRESS:
        raise ValidationError("Trip must be IN_PROGRESS.")

    if urole(user) != UserRole.ADMIN and trip.driver_id != user.id:
        raise PermissionDenied("This group is not assigned to your trip.")

    return trip, link.sequence_number


def _has_unfinished_previous_groups(trip, current_seq: int) -> bool:
    unfinished = (
        TripDispatchGroup.objects
        .select_related("group")
        .filter(trip=trip, sequence_number__lt=current_seq)
        .exclude(group__status__in=[DispatchGroupStatus.DROPPED_OFF, DispatchGroupStatus.OPENED])
        .first()
    )
    return unfinished is not None


def _allowed_statuses_for_group_from_location(group: DispatchGroup):
    t = group.from_location.type
    if t == LocationType.POST_OFFICE:
        return {ShipmentStatus.AT_POST_OFFICE}
    if t == LocationType.SORTING_CITY:
        return {ShipmentStatus.SORTED_WAITING_FOR_DISPATCH}
    if t == LocationType.DISTRIBUTION_CENTER:
        return {ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE}
    return set()


class DispatchGroupViewSet(ModelViewSet):
    queryset = DispatchGroup.objects.select_related(
        "from_location",
        "to_location",
        "created_by",
        "pickup_driver",
        "pickup_employee",
        "dropoff_driver",
        "dropoff_employee",
    ).all()
    serializer_class = DispatchGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return DispatchGroupCreateSerializer
        return DispatchGroupSerializer

    def perform_create(self, serializer):
        u = self.request.user
        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            raise PermissionDenied("Not allowed.")

        from_loc = _require_assigned_location(u)

        # to_location можна не передавати — підставляємо автоматично (PO->SC, SC->DC)
        to_loc = serializer.validated_data.get("to_location")
        if not to_loc:
            if from_loc.type == LocationType.POST_OFFICE:
                if not getattr(from_loc, "parent_sc", None):
                    raise ValidationError("Post office has no parent_sc.")
                to_loc = from_loc.parent_sc

            elif from_loc.type == LocationType.SORTING_CITY:
                if not getattr(from_loc, "parent_dc", None):
                    raise ValidationError("Sorting city has no parent_dc.")
                to_loc = from_loc.parent_dc

            else:
                raise ValidationError("For DC create groups via mark-sorted auto-generation.")

        serializer.save(created_by=u, from_location=from_loc, to_location=to_loc)

    # -----------------------
    # ADD / REMOVE shipments (тільки коли group CREATED)
    # -----------------------
    @action(detail=True, methods=["post"], url_path="add-shipments")
    def add_shipments(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only worker/admin can modify group items."}, status=403)

        if group.status != DispatchGroupStatus.CREATED:
            return Response({"detail": "You can add shipments only when group status is CREATED."}, status=400)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.from_location_id:
                return Response({"detail": "Employee must be assigned to from_location."}, status=403)

        shipment_ids = request.data.get("shipment_ids", [])
        if not isinstance(shipment_ids, list) or not shipment_ids:
            return Response({"detail": "shipment_ids must be a non-empty list."}, status=400)

        shipment_ids = list(dict.fromkeys([int(x) for x in shipment_ids]))

        existing_ids = set(Shipment.objects.filter(id__in=shipment_ids).values_list("id", flat=True))
        missing = [sid for sid in shipment_ids if sid not in existing_ids]
        if missing:
            return Response({"detail": f"Shipments not found: {missing[:10]}"}, status=400)

        active_statuses = {
            DispatchGroupStatus.CREATED,
            DispatchGroupStatus.SEALED,
            DispatchGroupStatus.IN_TRANSIT,
            DispatchGroupStatus.DROPPED_OFF,
        }
        already_in_active = set(
            DispatchGroupItem.objects.filter(
                shipment_id__in=shipment_ids,
                group__status__in=active_statuses,
            ).exclude(group_id=group.id).values_list("shipment_id", flat=True).distinct()
        )
        if already_in_active:
            return Response(
                {"detail": f"Some shipments already belong to an active group: {sorted(list(already_in_active))[:10]}"},
                status=400
            )

        allowed_statuses = _allowed_statuses_for_group_from_location(group)
        if not allowed_statuses:
            return Response({"detail": "Unsupported from_location type for grouping."}, status=400)

        bad = list(
            Shipment.objects.filter(id__in=shipment_ids)
            .exclude(status__in=allowed_statuses)
            .values_list("tracking_code", "status")[:5]
        )
        if bad:
            sample = ", ".join([f"{code}:{st}" for code, st in bad])
            return Response({"detail": f"Some shipments have invalid status for this group: {sample}"}, status=400)

        already_in_this_group = set(
            group.items.filter(shipment_id__in=shipment_ids).values_list("shipment_id", flat=True)
        )
        to_add = [sid for sid in shipment_ids if sid not in already_in_this_group]
        if not to_add:
            return Response({"detail": "All provided shipments are already in this group."}, status=200)

        with transaction.atomic():
            DispatchGroupItem.objects.bulk_create(
                [DispatchGroupItem(group=group, shipment_id=sid) for sid in to_add]
            )

        group.refresh_from_db()
        return Response(DispatchGroupSerializer(group).data)

    @action(detail=True, methods=["post"], url_path="remove-shipments")
    def remove_shipments(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only worker/admin can modify group items."}, status=403)

        if group.status != DispatchGroupStatus.CREATED:
            return Response({"detail": "You can remove shipments only when group status is CREATED."}, status=400)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.from_location_id:
                return Response({"detail": "Employee must be assigned to from_location."}, status=403)

        shipment_ids = request.data.get("shipment_ids", [])
        if not isinstance(shipment_ids, list) or not shipment_ids:
            return Response({"detail": "shipment_ids must be a non-empty list."}, status=400)

        shipment_ids = list(dict.fromkeys([int(x) for x in shipment_ids]))

        with transaction.atomic():
            deleted, _ = DispatchGroupItem.objects.filter(group=group, shipment_id__in=shipment_ids).delete()

        group.refresh_from_db()
        return Response({
            "detail": f"Removed {deleted} items.",
            "group": DispatchGroupSerializer(group).data
        })

    # -----------------------
    # Group lifecycle
    # -----------------------
    @action(detail=True, methods=["post"], url_path="seal")
    def seal(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Not allowed."}, status=403)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.from_location_id:
                return Response({"detail": "Employee must be assigned to from_location."}, status=403)

        try:
            group.seal()
        except Exception as e:
            raise ValidationError(str(e))

        return Response(DispatchGroupSerializer(group).data)

    # PICKUP: driver then employee
    @action(detail=True, methods=["post"], url_path="confirm-pickup-driver")
    def confirm_pickup_driver(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.DRIVER, UserRole.ADMIN):
            return Response({"detail": "Only driver/admin can confirm pickup."}, status=403)

        if group.status != DispatchGroupStatus.SEALED:
            return Response({"detail": "Group must be SEALED."}, status=400)

        if urole(u) != UserRole.ADMIN:
            trip, seq = _ensure_driver_can_act_on_group(u, group)
            if _has_unfinished_previous_groups(trip, seq):
                return Response({"detail": "Previous groups are not completed yet."}, status=400)

        if group.pickup_driver_id and group.pickup_driver_id != u.id and urole(u) != UserRole.ADMIN:
            return Response({"detail": "Pickup already confirmed by another driver."}, status=400)

        group.pickup_driver = u
        group.pickup_at = group.pickup_at or timezone.now()
        group.save(update_fields=["pickup_driver", "pickup_at"])

        return Response(DispatchGroupSerializer(group).data)

    @action(detail=True, methods=["post"], url_path="confirm-pickup-employee")
    def confirm_pickup_employee(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only worker/admin can confirm pickup."}, status=403)

        if group.status != DispatchGroupStatus.SEALED:
            return Response({"detail": "Group must be SEALED."}, status=400)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.from_location_id:
                return Response({"detail": "Employee must be assigned to from_location."}, status=403)

        if not group.pickup_driver_id and urole(u) != UserRole.ADMIN:
            return Response({"detail": "Driver must confirm pickup first."}, status=400)

        group.pickup_employee = u
        group.pickup_at = group.pickup_at or timezone.now()
        group.save(update_fields=["pickup_employee", "pickup_at"])

        try:
            group.on_pickup_fully_confirmed(changed_by_employee=u)
        except Exception as e:
            raise ValidationError(str(e))

        return Response(DispatchGroupSerializer(group).data)

    # DROPOFF: driver then employee
    @action(detail=True, methods=["post"], url_path="confirm-dropoff-driver")
    def confirm_dropoff_driver(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.DRIVER, UserRole.ADMIN):
            return Response({"detail": "Only driver/admin can confirm dropoff."}, status=403)

        if group.status != DispatchGroupStatus.IN_TRANSIT:
            return Response({"detail": "Group must be IN_TRANSIT."}, status=400)

        if urole(u) != UserRole.ADMIN:
            trip, seq = _ensure_driver_can_act_on_group(u, group)
            if _has_unfinished_previous_groups(trip, seq):
                return Response({"detail": "Previous groups are not completed yet."}, status=400)

        if group.dropoff_driver_id and group.dropoff_driver_id != u.id and urole(u) != UserRole.ADMIN:
            return Response({"detail": "Dropoff already confirmed by another driver."}, status=400)

        group.dropoff_driver = u
        group.dropoff_at = group.dropoff_at or timezone.now()
        group.save(update_fields=["dropoff_driver", "dropoff_at"])

        return Response(DispatchGroupSerializer(group).data)

    @action(detail=True, methods=["post"], url_path="confirm-dropoff-employee")
    def confirm_dropoff_employee(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only worker/admin can confirm dropoff."}, status=403)

        if group.status != DispatchGroupStatus.IN_TRANSIT:
            return Response({"detail": "Group must be IN_TRANSIT."}, status=400)

        if not group.dropoff_driver_id and urole(u) != UserRole.ADMIN:
            return Response({"detail": "Driver must confirm dropoff first."}, status=400)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.to_location_id:
                return Response({"detail": "Employee must be assigned to to_location."}, status=403)

        group.dropoff_employee = u
        group.dropoff_at = group.dropoff_at or timezone.now()
        group.save(update_fields=["dropoff_employee", "dropoff_at"])

        try:
            group.on_dropoff_fully_confirmed(changed_by_employee=u)
        except Exception as e:
            raise ValidationError(str(e))

        return Response(DispatchGroupSerializer(group).data)

    # OPEN
    @action(detail=True, methods=["post"], url_path="open")
    def open(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Not allowed."}, status=403)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.to_location_id:
                return Response({"detail": "Employee must be assigned to to_location."}, status=403)

        try:
            group.open_group()
        except Exception as e:
            raise ValidationError(str(e))

        return Response(DispatchGroupSerializer(group).data)

    # SORT + next groups
    @action(detail=True, methods=["post"], url_path="mark-sorted")
    def mark_sorted(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.WAREHOUSE_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only warehouse/admin can sort."}, status=403)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.to_location_id:
                return Response({"detail": "Employee must be assigned to to_location."}, status=403)

        try:
            group.mark_sorted(employee_user=u)
            next_groups = group.create_next_groups_after_sort(created_by_employee=u)
        except Exception as e:
            raise ValidationError(str(e))

        return Response({
            "sorted_group": DispatchGroupSerializer(group).data,
            "next_groups": [
                {
                    "id": g.id,
                    "group_code": g.group_code,
                    "from_code": g.from_location.code,
                    "to_code": g.to_location.code,
                    "status": g.status,
                    "items_count": g.items.count(),
                }
                for g in next_groups
            ],
        })

    # READY_FOR_PICKUP
    @action(detail=True, methods=["post"], url_path="mark-ready-for-pickup")
    def mark_ready_for_pickup(self, request, pk=None):
        group = self.get_object()
        u = request.user

        if urole(u) not in (UserRole.POSTAL_WORKER, UserRole.ADMIN):
            return Response({"detail": "Only postal/admin can do this."}, status=403)

        if urole(u) != UserRole.ADMIN:
            loc = _require_assigned_location(u)
            if loc.id != group.to_location_id:
                return Response({"detail": "Employee must be assigned to to_location."}, status=403)

        try:
            group.mark_ready_for_pickup(employee_user=u)
        except Exception as e:
            raise ValidationError(str(e))

        return Response(DispatchGroupSerializer(group).data)
