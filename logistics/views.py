from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.models import UserRole
from shipments.models import Shipment

from dispatch.models import DispatchGroup, DispatchGroupStatus
from .models import Truck, RoutePlan, RouteStop, Trip, TripDispatchGroup, TripStatus
from .serializers import (
    TruckSerializer,
    RoutePlanSerializer,
    RouteStopSerializer,
    TripSerializer,
    TripDispatchGroupSerializer,
)
from .services import build_route


def urole(user):
    return getattr(user, "role", "customer")


# ----------------------------
# TRUCK
# ----------------------------
class TruckViewSet(ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can create trucks.")
        serializer.save()

    def perform_update(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can update trucks.")
        serializer.save()

    def perform_destroy(self, instance):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can delete trucks.")
        instance.delete()


# ----------------------------
# ROUTE PLAN
# ----------------------------
class RoutePlanViewSet(ModelViewSet):
    queryset = RoutePlan.objects.prefetch_related("stops").all()
    serializer_class = RoutePlanSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can create route plans.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can update route plans.")
        serializer.save()

    def perform_destroy(self, instance):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can delete route plans.")
        instance.delete()

    @action(detail=False, methods=["get"], url_path=r"preview-for-shipment/(?P<shipment_id>\d+)")
    def preview_for_shipment(self, request, shipment_id=None):
        if urole(request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can preview routes.")

        sh = Shipment.objects.select_related(
            "origin",
            "destination",
            "origin__parent_sc",
            "destination__parent_sc",
            "origin__parent_sc__parent_dc",
            "destination__parent_sc__parent_dc",
        ).get(id=shipment_id)

        route = build_route(sh.origin, sh.destination)

        return Response({
            "shipment": sh.tracking_code,
            "route": [{"id": loc.id, "code": loc.code, "type": loc.type, "name": loc.name} for loc in route]
        })


# ----------------------------
# ROUTE STOP
# ----------------------------
class RouteStopViewSet(ModelViewSet):
    queryset = RouteStop.objects.select_related("route_plan", "location").all()
    serializer_class = RouteStopSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can create route stops.")
        serializer.save()

    def perform_update(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can update route stops.")
        serializer.save()

    def perform_destroy(self, instance):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can delete route stops.")
        instance.delete()


# ----------------------------
# TRIP
# ----------------------------
class TripViewSet(ModelViewSet):
    queryset = Trip.objects.select_related("driver", "truck", "route_plan").all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can create trips.")

        driver = serializer.validated_data["driver"]
        truck = serializer.validated_data["truck"]

        if urole(driver) not in (UserRole.DRIVER, UserRole.ADMIN):
            raise ValidationError("Selected driver must have DRIVER role.")

        if not truck.is_available:
            raise ValidationError("Truck is not available.")

        if Trip.objects.filter(driver=driver, status=TripStatus.IN_PROGRESS).exists():
            raise ValidationError("Driver already has an active trip.")

        serializer.save()

    def perform_update(self, serializer):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can update trips.")
        serializer.save()

    def perform_destroy(self, instance):
        if urole(self.request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can delete trips.")
        if instance.status == TripStatus.IN_PROGRESS:
            raise ValidationError("Cannot delete trip that is IN_PROGRESS.")
        instance.delete()

    @action(detail=True, methods=["get"], url_path="suggest-groups")
    def suggest_groups(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can view suggestions.")

        stops = list(trip.route_plan.stops.select_related("location").order_by("sequence_number"))
        if len(stops) < 2:
            raise ValidationError("RoutePlan must have at least 2 stops.")

        edges = []
        for i in range(len(stops) - 1):
            a = stops[i].location
            b = stops[i + 1].location
            edges.append((a.id, b.id, a.code, b.code))

        candidates = DispatchGroup.objects.select_related("from_location", "to_location").filter(
            status=DispatchGroupStatus.SEALED,
            pickup_driver__isnull=True,
            pickup_employee__isnull=True,
            dropoff_driver__isnull=True,
            dropoff_employee__isnull=True,
        )

        edge_index = {(a, b): idx for idx, (a, b, _, _) in enumerate(edges)}

        matched = []
        for g in candidates:
            key = (g.from_location_id, g.to_location_id)
            if key in edge_index:
                matched.append((edge_index[key], g))

        matched.sort(key=lambda x: x[0])

        return Response({
            "trip": trip.trip_code,
            "route_edges": [{"from": a, "to": b, "from_code": ac, "to_code": bc} for (a, b, ac, bc) in edges],
            "suggested_groups": [
                {
                    "edge_order": idx,
                    "group_id": g.id,
                    "group_code": g.group_code,
                    "from_code": g.from_location.code,
                    "to_code": g.to_location.code,
                    "status": g.status,
                    "items_count": g.items.count(),
                }
                for (idx, g) in matched
            ],
        })

    @action(detail=True, methods=["post"], url_path="attach-suggested-groups")
    def attach_suggested_groups(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can attach groups.")

        stops = list(trip.route_plan.stops.select_related("location").order_by("sequence_number"))
        if len(stops) < 2:
            raise ValidationError("RoutePlan must have at least 2 stops.")

        edges = [(stops[i].location_id, stops[i + 1].location_id) for i in range(len(stops) - 1)]

        # зайняті sequence у рейсі
        used_seq = set(
            TripDispatchGroup.objects.filter(trip=trip).values_list("sequence_number", flat=True)
        )

        edge_index = {edge: idx + 1 for idx, edge in enumerate(edges)}  # базовий порядок зупинок

        candidates = DispatchGroup.objects.select_related("from_location", "to_location").filter(
            status=DispatchGroupStatus.SEALED,
            pickup_driver__isnull=True,
            pickup_employee__isnull=True,
            dropoff_driver__isnull=True,
            dropoff_employee__isnull=True,
        )

        attached = []
        for g in candidates:
            edge = (g.from_location_id, g.to_location_id)
            if edge not in edge_index:
                continue

            # одна група не може бути в двох рейсах
            if hasattr(g, "trip_link"):
                continue

            base_seq = edge_index[edge]
            seq = base_seq
            while seq in used_seq:
                seq += 100  # щоб зберегти порядок ребер, але уникнути конфлікту
            used_seq.add(seq)

            obj, created = TripDispatchGroup.objects.get_or_create(
                trip=trip,
                group=g,
                defaults={"sequence_number": seq},
            )
            if created:
                attached.append({"group_code": g.group_code, "sequence_number": seq})

        attached.sort(key=lambda x: x["sequence_number"])
        return Response({"trip": trip.trip_code, "attached": attached})

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.DRIVER, UserRole.ADMIN):
            return Response({"detail": "Only driver/admin can start trip."}, status=403)

        if urole(request.user) != UserRole.ADMIN and trip.driver_id != request.user.id:
            return Response({"detail": "You can start only your own trip."}, status=403)

        if not trip.trip_groups.exists():
            return Response({"detail": "Trip has no assigned dispatch groups."}, status=400)

        if trip.status != TripStatus.PLANNED:
            return Response({"detail": "Trip can be started only from PLANNED."}, status=400)

        with transaction.atomic():
            truck = type(trip.truck).objects.select_for_update().get(id=trip.truck_id)
            if not truck.is_available:
                return Response({"detail": "Truck is not available."}, status=400)

            truck.is_available = False
            truck.save(update_fields=["is_available"])

            trip.status = TripStatus.IN_PROGRESS
            trip.started_at = trip.started_at or timezone.now()
            trip.save(update_fields=["status", "started_at"])

        return Response(TripSerializer(trip).data)

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.DRIVER, UserRole.ADMIN):
            return Response({"detail": "Only driver/admin can finish trip."}, status=403)

        if urole(request.user) != UserRole.ADMIN and trip.driver_id != request.user.id:
            return Response({"detail": "You can finish only your own trip."}, status=403)

        if trip.status != TripStatus.IN_PROGRESS:
            return Response({"detail": "Trip can be finished only from IN_PROGRESS."}, status=400)

        with transaction.atomic():
            truck = type(trip.truck).objects.select_for_update().get(id=trip.truck_id)

            trip.status = TripStatus.COMPLETED
            trip.finished_at = trip.finished_at or timezone.now()
            trip.save(update_fields=["status", "finished_at"])

            truck.is_available = True
            truck.save(update_fields=["is_available"])

        return Response(TripSerializer(trip).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can cancel trip.")

        if trip.status == TripStatus.COMPLETED:
            raise ValidationError("Completed trip cannot be canceled.")

        with transaction.atomic():
            truck = type(trip.truck).objects.select_for_update().get(id=trip.truck_id)

            trip.status = TripStatus.CANCELED
            trip.save(update_fields=["status"])

            # звільняємо truck
            truck.is_available = True
            truck.save(update_fields=["is_available"])

        return Response(TripSerializer(trip).data)


    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        trip = self.get_object()

        if urole(request.user) not in (UserRole.LOGIST, UserRole.ADMIN, UserRole.DRIVER):
            raise PermissionDenied("Not allowed.")

        # Водій бачить тільки свій рейс (admin/logist — всі)
        if urole(request.user) == UserRole.DRIVER and trip.driver_id != request.user.id:
            return Response({"detail": "You can view only your own trip."}, status=403)

        stops = list(trip.route_plan.stops.select_related("location").order_by("sequence_number"))

        tgs = list(
            trip.trip_groups.select_related(
                "group",
                "group__from_location",
                "group__to_location",
            ).order_by("sequence_number")
        )

        groups_data = []
        for tg in tgs:
            g = tg.group
            groups_data.append({
                "seq": tg.sequence_number,
                "group_id": g.id,
                "group_code": g.group_code,
                "status": g.status,
                "from_code": g.from_location.code,
                "to_code": g.to_location.code,
                "pickup_driver_id": g.pickup_driver_id,
                "pickup_employee_id": g.pickup_employee_id,
                "pickup_at": g.pickup_at,
                "dropoff_driver_id": g.dropoff_driver_id,
                "dropoff_employee_id": g.dropoff_employee_id,
                "dropoff_at": g.dropoff_at,
            })

        # Визначаємо поточну групу (перша незавершена)
        finished_statuses = {DispatchGroupStatus.DROPPED_OFF, DispatchGroupStatus.OPENED}
        current = None
        for item in groups_data:
            if item["status"] not in finished_statuses:
                current = item
                break

        total = len(groups_data)
        finished = sum(1 for x in groups_data if x["status"] in finished_statuses)
        progress_percent = int((finished / total) * 100) if total else 0

        return Response({
            "trip_code": trip.trip_code,
            "trip_status": trip.status,
            "driver_id": trip.driver_id,
            "truck_id": trip.truck_id,
            "started_at": trip.started_at,
            "finished_at": trip.finished_at,
            "route_stops": [
                {"seq": s.sequence_number, "location_id": s.location_id, "code": s.location.code, "type": s.location.type, "name": s.location.name}
                for s in stops
            ],
            "groups": groups_data,
            "current_group": current,
            "progress_percent": progress_percent,
        })


# ----------------------------
# TRIP DISPATCH GROUP (attach group to trip)
# ----------------------------
class TripDispatchGroupViewSet(ModelViewSet):
    queryset = TripDispatchGroup.objects.select_related("trip", "group").all()
    serializer_class = TripDispatchGroupSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        u = self.request.user
        if urole(u) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can attach groups to trip.")

        trip = serializer.validated_data["trip"]

        seq = serializer.validated_data.get("sequence_number")
        if not seq:
            last = TripDispatchGroup.objects.filter(trip=trip).aggregate(m=Max("sequence_number"))["m"] or 0
            seq = last + 1

        serializer.save(sequence_number=seq)

    def perform_destroy(self, instance):
        u = self.request.user
        if urole(u) not in (UserRole.LOGIST, UserRole.ADMIN):
            raise PermissionDenied("Only logist/admin can detach groups.")
        # не можна відривати, якщо рейс вже в дорозі
        if instance.trip.status == TripStatus.IN_PROGRESS:
            raise ValidationError("Cannot detach groups from IN_PROGRESS trip.")
        instance.delete()
