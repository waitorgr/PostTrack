from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Shipment, Payment, ShipmentStatus, PaymentType
from .serializers import (
    ShipmentListSerializer, ShipmentCreateSerializer,
    ShipmentDetailSerializer, ShipmentStatusUpdateSerializer,
)
from accounts.permissions import IsPostalWorker, IsPostalOrWarehouse, IsStaff
from tracking.utils import create_tracking_event


class ShipmentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [IsPostalWorker()]
        return [IsStaff()]

    def get_serializer_class(self):
        if self.action == 'create':
            return ShipmentCreateSerializer
        if self.action in ('list',):
            return ShipmentListSerializer
        return ShipmentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        from accounts.models import Role
        qs = Shipment.objects.select_related('origin', 'destination', 'created_by', 'payment')

        if user.role == Role.POSTAL_WORKER:
            # бачить тільки посилки свого відділення
            qs = qs.filter(origin=user.location) | qs.filter(destination=user.location)
        elif user.role in (Role.SORTING_CENTER_WORKER, Role.DISTRIBUTION_CENTER_WORKER):
            # посилки на своєму складі (через dispatch)
            from dispatch.models import DispatchGroupItem
            shipment_ids = DispatchGroupItem.objects.filter(
                group__current_location=user.location
            ).values_list('shipment_id', flat=True)
            qs = qs.filter(id__in=shipment_ids)
        elif user.role == Role.CUSTOMER:
            # клієнт не має доступу через цей endpoint
            qs = qs.none()
        # logist, admin — всі посилки

        # фільтри
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(tracking_number__icontains=search)

        return qs.distinct()

    def perform_create(self, serializer):
        user = self.request.user
        shipment = serializer.save(
            origin=user.location,
            created_by=user,
        )
        # Створюємо запис оплати
        Payment.objects.create(
            shipment=shipment,
            amount=shipment.price,
            is_paid=(shipment.payment_type == PaymentType.PREPAID),
        )
        # Трекінг-подія
        create_tracking_event(
            shipment=shipment,
            event_type='accepted',
            location=user.location,
            created_by=user,
            note='Посилку прийнято та зареєстровано у системі.',
            is_public=True,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsPostalOrWarehouse])
    def update_status(self, request, pk=None):
        """POST /api/shipments/<id>/update_status/"""
        shipment = self.get_object()
        serializer = ShipmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')

        shipment.status = new_status
        shipment.save()

        create_tracking_event(
            shipment=shipment,
            event_type=new_status,
            location=request.user.location,
            created_by=request.user,
            note=note,
            is_public=True,
        )
        return Response(ShipmentDetailSerializer(shipment).data)

    @action(detail=True, methods=['post'], permission_classes=[IsPostalOrWarehouse])
    def cancel(self, request, pk=None):
        """POST /api/shipments/<id>/cancel/"""
        shipment = self.get_object()
        if shipment.status in (ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED, ShipmentStatus.RETURNED):
            return Response(
                {'detail': 'Неможливо скасувати посилку в поточному статусі.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shipment.status = ShipmentStatus.CANCELLED
        shipment.save()
        create_tracking_event(
            shipment=shipment,
            event_type='cancelled',
            location=request.user.location,
            created_by=request.user,
            note=request.data.get('reason', 'Посилку скасовано.'),
            is_public=True,
        )
        return Response({'detail': 'Посилку скасовано.'})

    @action(detail=True, methods=['post'], permission_classes=[IsPostalWorker])
    def confirm_delivery(self, request, pk=None):
        """POST /api/shipments/<id>/confirm_delivery/ — підтвердження доставки."""
        shipment = self.get_object()
        if shipment.status == ShipmentStatus.DELIVERED:
            return Response({'detail': 'Вже доставлено.'}, status=status.HTTP_400_BAD_REQUEST)
        shipment.status = ShipmentStatus.DELIVERED
        shipment.save()
        # Якщо cash_on_delivery — підтверджуємо оплату
        if shipment.payment_type == PaymentType.CASH_ON_DELIVERY:
            payment, _ = Payment.objects.get_or_create(
                shipment=shipment, defaults={'amount': shipment.price}
            )
            payment.is_paid = True
            payment.paid_at = timezone.now()
            payment.received_by = request.user
            payment.save()
        create_tracking_event(
            shipment=shipment,
            event_type='delivered',
            location=request.user.location,
            created_by=request.user,
            note='Посилку доставлено отримувачу.',
            is_public=True,
        )
        return Response(ShipmentDetailSerializer(shipment).data)

    @action(detail=True, methods=['post'], permission_classes=[IsPostalWorker])
    def confirm_payment(self, request, pk=None):
        """POST /api/shipments/<id>/confirm_payment/ — ручне підтвердження оплати."""
        shipment = self.get_object()
        payment, _ = Payment.objects.get_or_create(
            shipment=shipment, defaults={'amount': shipment.price}
        )
        if payment.is_paid:
            return Response({'detail': 'Вже оплачено.'}, status=status.HTTP_400_BAD_REQUEST)
        payment.is_paid = True
        payment.paid_at = timezone.now()
        payment.received_by = request.user
        payment.save()
        return Response({'detail': 'Оплату підтверджено.'})
