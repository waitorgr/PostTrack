from django.db.models import Count, Q
from django.http import FileResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsPostalOrWarehouse
from reports.pdf_generator import (
    generate_dispatch_arrive_report,
    generate_dispatch_depart_report,
)

from .models import DispatchGroup
from .serializers import (
    AddShipmentSerializer,
    DispatchGroupCreateSerializer,
    DispatchGroupDetailSerializer,
    DispatchGroupListSerializer,
)
from .services import DispatchService


def _normalize_role(value):
    if value is None:
        return ''

    if hasattr(value, 'value'):
        value = value.value

    return str(value).strip().lower()


def _is_admin_like(user):
    if not user or not user.is_authenticated:
        return False

    if getattr(user, 'is_superuser', False):
        return True

    return _normalize_role(getattr(user, 'role', None)) == 'admin'


def _is_logist(user):
    if not user or not user.is_authenticated:
        return False

    if _is_admin_like(user):
        return True

    role = _normalize_role(getattr(user, 'role', None))
    return role in {'logist', 'logistics', 'logistician'}


class DispatchGroupAccessPermission(permissions.BasePermission):
    """
    Безпечна схема доступу:
    - admin/superuser: повний доступ
    - logist: тільки list/retrieve
    - postal/warehouse: як і раніше, повний доступ через IsPostalOrWarehouse
    """
    postal_or_warehouse_permission = IsPostalOrWarehouse()

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if _is_admin_like(user):
            return True

        if _is_logist(user):
            return view.action in {'list', 'retrieve'}

        return self.postal_or_warehouse_permission.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if _is_admin_like(user):
            return True

        if _is_logist(user):
            return view.action in {'retrieve'}

        permission = self.postal_or_warehouse_permission

        if hasattr(permission, 'has_object_permission'):
            return permission.has_object_permission(request, view, obj)

        return permission.has_permission(request, view)


class DispatchGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [DispatchGroupAccessPermission]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return DispatchGroupCreateSerializer
        if self.action == 'retrieve':
            return DispatchGroupDetailSerializer
        return DispatchGroupListSerializer
    
    @action(detail=False, methods=['post'])
    def add_shipment_auto(self, request):
        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['shipment']
    
        try:
            group, _ = DispatchService.get_or_create_open_group_for_shipment(
                shipment=shipment,
                created_by=request.user,
            )
            DispatchService.add_shipment(
                group=group,
                shipment=shipment,
                added_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)
    
        return self._detail_response(group, status_code=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def create_with_shipment(self, request):
        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['shipment']
    
        try:
            group, _ = DispatchService.get_or_create_open_group_for_shipment(
                shipment=shipment,
                created_by=request.user,
            )
    
            DispatchService.add_shipment(
                group=group,
                shipment=shipment,
                added_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)
    
        return self._detail_response(group, status_code=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user

        qs = (
            DispatchGroup.objects.select_related(
                'origin',
                'destination',
                'current_location',
                'driver',
                'created_by',
            )
            .prefetch_related(
                'items__shipment',
                'items__added_by',
            )
            .annotate(_items_count=Count('items'))
        )

        # Логіст / адмін бачать overview по всіх групах
        if not (_is_logist(user) or _is_admin_like(user)):
            location = getattr(user, 'location', None)
            if not location:
                return qs.none()

            scope = (self.request.query_params.get('scope') or '').strip().lower()
            role = _normalize_role(getattr(user, 'role', None))

            if scope == 'incoming':
                qs = qs.filter(destination=location)
            elif scope == 'outgoing':
                qs = qs.filter(origin=location)
            elif scope == 'current':
                qs = qs.filter(current_location=location)
            elif role == 'postal_worker':
                qs = qs.filter(origin=location)
            else:
                qs = qs.filter(current_location=location)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = (self.request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(origin__name__icontains=search) |
                Q(destination__name__icontains=search)
            )

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save()

    def _detail_response(self, group, status_code=status.HTTP_200_OK):
        group.refresh_from_db()
        serializer = DispatchGroupDetailSerializer(
            group,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status_code)

    def _service_error_response(self, exc):
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=['post'])
    def add_shipment(self, request, pk=None):
        group = self.get_object()

        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['shipment']

        try:
            DispatchService.add_shipment(
                group=group,
                shipment=shipment,
                added_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(group)

    @action(detail=True, methods=['post'])
    def remove_shipment(self, request, pk=None):
        group = self.get_object()

        serializer = AddShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.validated_data['shipment']

        try:
            DispatchService.remove_shipment(
                group=group,
                shipment=shipment,
                removed_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(group)

    @action(detail=True, methods=['post'])
    def mark_ready(self, request, pk=None):
        group = self.get_object()

        try:
            DispatchService.mark_ready(
                group=group,
                marked_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(group)

    @action(detail=True, methods=['post'])
    def depart(self, request, pk=None):
        group = self.get_object()

        try:
            updated_group = DispatchService.depart(
                group=group,
                departed_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        updated_group.refresh_from_db()
        buffer = generate_dispatch_depart_report(updated_group, handed_by=request.user)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'dispatch_depart_{updated_group.code}.pdf',
            content_type='application/pdf',
        )

    @action(detail=True, methods=['post'])
    def arrive(self, request, pk=None):
        group = self.get_object()

        try:
            updated_group = DispatchService.arrive(
                group=group,
                arrived_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        updated_group.refresh_from_db()
        buffer = generate_dispatch_arrive_report(updated_group, received_by=request.user)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'dispatch_arrive_{updated_group.code}.pdf',
            content_type='application/pdf',
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        group = self.get_object()

        try:
            DispatchService.complete(
                group=group,
                completed_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(group)
    
    