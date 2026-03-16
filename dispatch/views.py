from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.http import FileResponse

from .models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus
from .serializers import (
    DispatchGroupListSerializer, DispatchGroupDetailSerializer,
    DispatchGroupCreateSerializer, AddShipmentSerializer,
)
from accounts.permissions import IsPostalOrWarehouse
from shipments.models import ShipmentStatus
from tracking.utils import create_tracking_event
from reports.pdf_generator import (
    generate_dispatch_depart_report,
    generate_dispatch_arrive_report,
)


class DispatchGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPostalOrWarehouse]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return DispatchGroupCreateSerializer
        if self.action == 'retrieve':
            return DispatchGroupDetailSerializer
        return DispatchGroupListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = DispatchGroup.objects.select_related('origin', 'destination').prefetch_related('items')
        # Бачить лише групи своєї локації
        if user.location:
            qs = qs.filter(origin=user.location)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        # Автоматично визначаємо destination на основі ієрархії
        destination = user.location.get_distribution_center() if hasattr(user.location, 'get_distribution_center') else None
        if user.location.type == 'distribution_center':
            destination = user.location.get_sorting_center()
        
        group = serializer.save(
            origin=user.location,
            destination=destination,
            current_location=user.location,
            created_by=user,
        )

    @action(detail=True, methods=['post'])
    def add_shipment(self, request, pk=None):
        """POST /api/dispatch/groups/<id>/add_shipment/"""
        group = self.get_object()
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            return Response(
                {'detail': 'Неможливо додати посилку — група вже відправлена.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['tracking_number']

        # Посилка має бути на тій самій локації
        if shipment.origin != group.origin and not DispatchGroupItem.objects.filter(
            shipment=shipment, group__destination=group.origin
        ).exists():
            pass  # допускаємо гнучко

        item, created = DispatchGroupItem.objects.get_or_create(
            group=group, shipment=shipment,
            defaults={'added_by': request.user}
        )
        if not created:
            return Response({'detail': 'Посилка вже в цій групі.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DispatchGroupDetailSerializer(group).data)

    @action(detail=True, methods=['post'])
    def remove_shipment(self, request, pk=None):
        """POST /api/dispatch/groups/<id>/remove_shipment/"""
        group = self.get_object()
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            return Response({'detail': 'Неможливо видалити — група вже відправлена.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['tracking_number']
        deleted, _ = DispatchGroupItem.objects.filter(group=group, shipment=shipment).delete()
        if not deleted:
            return Response({'detail': 'Посилку не знайдено в цій групі.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DispatchGroupDetailSerializer(group).data)

    @action(detail=True, methods=['post'])
    def mark_ready(self, request, pk=None):
        """POST /api/dispatch/groups/<id>/mark_ready/ — готово до відправки."""
        group = self.get_object()
        group.status = DispatchGroupStatus.READY
        group.save()
        return Response(DispatchGroupDetailSerializer(group).data)

    @action(detail=True, methods=['post'])
    def depart(self, request, pk=None):
        """POST /api/dispatch/groups/<id>/depart/ — підтвердження відправки з генерацією звіту."""
        group = self.get_object()
        if group.status != DispatchGroupStatus.READY:
            return Response({'detail': 'Група ще не готова до відправки.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Оновлюємо статус групи
        group.status = DispatchGroupStatus.IN_TRANSIT
        group.departed_at = timezone.now()
        group.save()

        # Оновлюємо статуси всіх посилок у групі
        for item in group.items.select_related('shipment'):
            item.shipment.status = ShipmentStatus.PICKED_UP_BY_DRIVER
            item.shipment.save()
            create_tracking_event(
                shipment=item.shipment,
                event_type='picked_up_by_driver',
                location=group.origin,
                created_by=request.user,
                note=f"Dispatch група {group.code}",
                is_public=True,
            )
        
        # Генеруємо звіт відправки
        buffer = generate_dispatch_depart_report(group, handed_by=request.user)
        
        # Повертаємо PDF файл
        return FileResponse(
            buffer, 
            as_attachment=True,
            filename=f"dispatch_depart_{group.code}.pdf",
            content_type='application/pdf'
        )

    @action(detail=True, methods=['post'])
    def arrive(self, request, pk=None):
        """POST /api/dispatch/groups/<id>/arrive/ — підтвердження прибуття з генерацією звіту."""
        group = self.get_object()
        if group.status != DispatchGroupStatus.IN_TRANSIT:
            return Response({'detail': 'Група не в дорозі.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Оновлюємо статус групи
        group.status = DispatchGroupStatus.ARRIVED
        group.arrived_at = timezone.now()
        group.current_location = group.destination
        group.save()

        # Оновлюємо статуси посилок
        for item in group.items.select_related('shipment'):
            item.shipment.status = ShipmentStatus.ARRIVED_AT_FACILITY
            item.shipment.save()
            create_tracking_event(
                shipment=item.shipment,
                event_type='arrived_at_facility',
                location=group.destination,
                created_by=request.user,
                note=f"Dispatch група {group.code} прибула до {group.destination.name}.",
                is_public=True,
            )
        
        # Генеруємо звіт прибуття
        buffer = generate_dispatch_arrive_report(group, received_by=request.user)
        
        # Повертаємо PDF файл
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"dispatch_arrive_{group.code}.pdf",
            content_type='application/pdf'
        )
