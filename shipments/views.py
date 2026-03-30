from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.models import Role
from accounts.permissions import IsPostalWorker, IsStaff
from dispatch.models import DispatchGroupItem

from .models import Shipment
from .serializers import (
    PaymentConfirmSerializer,
    ShipmentCancelSerializer,
    ShipmentCreateSerializer,
    ShipmentDetailSerializer,
    ShipmentListSerializer,
    ShipmentReturnSerializer,
    ShipmentStatusUpdateSerializer,
)
from .services import ShipmentService
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.permissions import AllowAny

class ShipmentViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "track":
            return [AllowAny()]
        if self.action == "create":
            return [IsPostalWorker()]
        return [IsStaff()]
    
    @action(
    detail=False,
    methods=["get"],
    url_path=r"track/(?P<tracking_number>[^/.]+)",
)
    def track(self, request, tracking_number=None):
        tracking_number = (tracking_number or "").strip()
    
        shipment = Shipment.objects.select_related(
            "origin",
            "destination",
            "created_by",
            "payment",
        ).filter(
            tracking_number__iexact=tracking_number
        ).first()
    
        if not shipment:
            return Response(
                {"detail": "Посилку з таким трек-номером не знайдено."},
                status=status.HTTP_404_NOT_FOUND,
            )
    
        return Response(
            ShipmentDetailSerializer(
                shipment,
                context=self.get_serializer_context(),
            ).data
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ShipmentCreateSerializer
        if self.action == "list":
            return ShipmentListSerializer
        if self.action == "update_status":
            return ShipmentStatusUpdateSerializer
        if self.action == "cancel":
            return ShipmentCancelSerializer
        if self.action == "confirm_payment":
            return PaymentConfirmSerializer
        if self.action == "return_shipment":
            return ShipmentReturnSerializer
        return ShipmentDetailSerializer

    def get_queryset(self):
        user = self.request.user

        qs = Shipment.objects.select_related(
            "origin",
            "destination",
            "created_by",
            "payment",
        )

        if user.role == Role.POSTAL_WORKER:
            qs = qs.filter(Q(origin=user.location) | Q(destination=user.location))

        elif user.role in (Role.SORTING_CENTER_WORKER, Role.DISTRIBUTION_CENTER_WORKER):
            shipment_ids = DispatchGroupItem.objects.filter(
                group__current_location=user.location
            ).values_list("shipment_id", flat=True)
            qs = qs.filter(id__in=shipment_ids)

        elif user.role == Role.CUSTOMER:
            qs = qs.none()

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(tracking_number__icontains=search)
                | Q(sender_first_name__icontains=search)
                | Q(sender_last_name__icontains=search)
                | Q(receiver_first_name__icontains=search)
                | Q(receiver_last_name__icontains=search)
                | Q(sender_phone__icontains=search)
                | Q(receiver_phone__icontains=search)
            )

        return qs.distinct()

    def _ensure_role(self, *allowed_roles):
        user = self.request.user
        if user.role not in allowed_roles:
            raise PermissionDenied("У вас немає прав для цієї дії.")

    def _serialize_detail(self, shipment: Shipment):
        return ShipmentDetailSerializer(
            shipment,
            context=self.get_serializer_context(),
        ).data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
    
        try:
            shipment = ShipmentService.create_shipment(
                data=serializer.validated_data,
                created_by=request.user,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(exc.message_dict)
            if hasattr(exc, "messages"):
                raise ValidationError({"detail": exc.messages})
            raise ValidationError({"detail": str(exc)})
    
        headers = self.get_success_headers({"tracking_number": shipment.tracking_number})
        return Response(
            self._serialize_detail(shipment),
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """
        POST /api/shipments/<id>/update_status/
        """
        self._ensure_role(
            Role.POSTAL_WORKER,
            Role.SORTING_CENTER_WORKER,
            Role.DISTRIBUTION_CENTER_WORKER,
            Role.ADMIN,
        )

        shipment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            shipment = ShipmentService.update_status(
                shipment=shipment,
                new_status=serializer.validated_data["status"],
                performed_by=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ValueError as exc:
            raise ValidationError({"status": str(exc)})

        return Response(self._serialize_detail(shipment))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        POST /api/shipments/<id>/cancel/
        """
        self._ensure_role(
            Role.POSTAL_WORKER,
            Role.SORTING_CENTER_WORKER,
            Role.DISTRIBUTION_CENTER_WORKER,
            Role.ADMIN,
        )

        shipment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            shipment = ShipmentService.cancel_shipment(
                shipment=shipment,
                reason=serializer.validated_data.get("reason", ""),
                cancelled_by=request.user,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})

        return Response(self._serialize_detail(shipment))

    @action(detail=True, methods=["post"])
    def confirm_delivery(self, request, pk=None):
        """
        POST /api/shipments/<id>/confirm_delivery/
        """
        self._ensure_role(Role.POSTAL_WORKER, Role.ADMIN)

        shipment = self.get_object()

        try:
            shipment = ShipmentService.confirm_delivery(
                shipment=shipment,
                confirmed_by=request.user,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})

        return Response(self._serialize_detail(shipment))

    @action(detail=True, methods=["post"])
    def confirm_payment(self, request, pk=None):
        """
        POST /api/shipments/<id>/confirm_payment/
        """
        self._ensure_role(Role.POSTAL_WORKER, Role.ADMIN)

        shipment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ShipmentService.confirm_payment(
                shipment=shipment,
                confirmed_by=request.user,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})

        shipment.refresh_from_db()
        return Response(self._serialize_detail(shipment))

    @action(detail=True, methods=["post"])
    def return_shipment(self, request, pk=None):
        """
        POST /api/shipments/<id>/return_shipment/
        """
        self._ensure_role(Role.POSTAL_WORKER, Role.ADMIN)

        shipment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            shipment = ShipmentService.initiate_return(
                shipment=shipment,
                reason=serializer.validated_data.get("reason", ""),
                initiated_by=request.user,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})

        return Response(self._serialize_detail(shipment))