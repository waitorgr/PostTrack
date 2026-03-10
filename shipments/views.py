import re

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework import status

from accounts.permissions import IsPostWorkerOrAdmin, IsWorker
from accounts.models import UserRole

from locations.models import LocationType
from tracking.models import TrackingEvent

from .models import Shipment
from .serializers import (
    ShipmentSerializer,
    ShipmentPublicBriefSerializer,
    ShipmentPublicTrackingSerializer,
)
from shipments.models import ShipmentStatus
from shipments.services import ShipmentService
from django.core.exceptions import ValidationError as DjangoValidationError



def _digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def _phone_matches(shipment: Shipment, phone: str | None, phone_last4: str | None) -> bool:
    sender = _digits(getattr(shipment, "sender_phone", ""))
    recip = _digits(getattr(shipment, "recipient_phone", ""))

    if not sender and not recip:
        return False

    if phone:
        p = _digits(phone)
        return bool(p) and (p == sender or p == recip)

    if phone_last4:
        last4 = _digits(phone_last4)[-4:]
        if len(last4) != 4:
            return False
        return sender.endswith(last4) or recip.endswith(last4)

    return False


class ShipmentViewSet(ModelViewSet):
    queryset = Shipment.objects.select_related("origin", "destination").all()
    serializer_class = ShipmentSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsPostWorkerOrAdmin()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsWorker()]
        if self.action == "track":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Anonymous для track не має лізти в фільтрацію
        if getattr(user, "is_anonymous", False):
            return qs

        if getattr(user, "role", "customer") == "customer":
            return qs.filter(created_by=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        user_loc = getattr(user, "assigned_location", None)
    
        if not user_loc or getattr(user_loc, "type", None) != LocationType.POST_OFFICE:
            raise ValidationError("User must be assigned to a Post Office to create shipment.")
    
        # ігноруємо origin з фронту (навіть якщо прийшов) — щоб не було махінацій
        shipment = serializer.save(created_by=user, origin=user_loc)
    
        # одразу ставимо статус "AT_POST_OFFICE" + TrackingEvent
        try:
            ShipmentService.set_status(
                shipment,
                ShipmentStatus.AT_POST_OFFICE,
                location=user_loc,
                actor_user=user,
                comment="Accepted at post office.",
            )
        except DjangoValidationError as e:
            raise ValidationError(str(e))

    @action(detail=False, methods=["get"], url_path=r"track/(?P<tracking_code>[^/.]+)")
    def track(self, request, tracking_code=None):
        try:
            shipment = Shipment.objects.select_related("origin", "destination").get(tracking_code=tracking_code)
        except Shipment.DoesNotExist:
            raise NotFound("Shipment not found.")

        phone = request.query_params.get("phone")
        phone_last4 = request.query_params.get("phone_last4")

        # Без телефону — короткий (публічний) перегляд
        if not phone and not phone_last4:
            return Response(ShipmentPublicBriefSerializer(shipment).data)

        # З телефоном — повний або 403
        if _phone_matches(shipment, phone, phone_last4):
            return Response(ShipmentPublicTrackingSerializer(shipment).data)

        return Response({"detail": "Phone verification failed."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="deliver")
    def deliver(self, request, pk=None):
        sh = self.get_object()
        u = request.user

        if getattr(u, "role", None) not in (UserRole.POSTAL_WORKER, UserRole.ADMIN):
            raise PermissionDenied("Only postal worker/admin can deliver shipments.")

        if not getattr(u, "assigned_location", None):
            raise ValidationError("User has no assigned_location.")

        if u.assigned_location.type != LocationType.POST_OFFICE:
            raise ValidationError("Delivery is allowed only at Post Office.")

        if u.role != UserRole.ADMIN and sh.destination_id != u.assigned_location_id:
            raise PermissionDenied("You can deliver only at destination post office.")

        if sh.status != ShipmentStatus.READY_FOR_PICKUP:
            raise ValidationError("Shipment must be READY_FOR_PICKUP to deliver.")

        comment = request.data.get("comment", "Delivered to recipient.")

        try:
            ShipmentService.set_status(
                sh,
                ShipmentStatus.DELIVERED,
                location=u.assigned_location,
                actor_user=u,
                comment=comment,
            )
        except DjangoValidationError as e:
            raise ValidationError(str(e))

        return Response({"tracking_code": sh.tracking_code, "status": sh.status})
