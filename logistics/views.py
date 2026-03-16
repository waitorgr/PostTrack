from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Route, RouteStatus
from .serializers import (
    RouteListSerializer, RouteDetailSerializer,
    RouteCreateSerializer, RouteUpdateSerializer,
)
from accounts.permissions import IsLogist, IsDriverOrLogist


class RouteViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsDriverOrLogist()]
        return [IsLogist()]

    def get_serializer_class(self):
        if self.action == 'create':
            return RouteCreateSerializer
        if self.action in ('update', 'partial_update'):
            return RouteUpdateSerializer
        if self.action == 'retrieve':
            return RouteDetailSerializer
        return RouteListSerializer

    def get_queryset(self):
        from accounts.models import Role
        user = self.request.user
        qs = Route.objects.select_related('driver', 'origin', 'destination', 'dispatch_group')
        if user.role == Role.DRIVER:
            qs = qs.filter(driver=user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """POST /api/logistics/routes/<id>/confirm/ — логіст підтверджує маршрут."""
        route = self.get_object()
        route.status = RouteStatus.CONFIRMED
        route.save()
        return Response(RouteDetailSerializer(route).data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """POST /api/logistics/routes/<id>/start/ — водій починає маршрут."""
        route = self.get_object()
        if route.status != RouteStatus.CONFIRMED:
            return Response({'detail': 'Маршрут не підтверджено.'}, status=status.HTTP_400_BAD_REQUEST)
        route.status = RouteStatus.IN_PROGRESS
        route.save()
        return Response(RouteDetailSerializer(route).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/logistics/routes/<id>/complete/"""
        route = self.get_object()
        route.status = RouteStatus.COMPLETED
        route.save()
        return Response(RouteDetailSerializer(route).data)
