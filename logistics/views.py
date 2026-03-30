from django.db.models import Count
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsDriverOrLogist, IsLogist
from .models import Route, RouteStatus
from .serializers import (
    RouteCreateSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RouteUpdateSerializer,
)
from .services import RouteService


class GenerateStepsInputSerializer(drf_serializers.Serializer):
    transit_location_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    replace_existing = drf_serializers.BooleanField(required=False, default=False)


class ReplaceStepsInputSerializer(drf_serializers.Serializer):
    location_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )


class AddStepInputSerializer(drf_serializers.Serializer):
    location = drf_serializers.IntegerField()
    order = drf_serializers.IntegerField(required=False, allow_null=True)
    planned_arrival = drf_serializers.DateTimeField(required=False, allow_null=True)
    planned_departure = drf_serializers.DateTimeField(required=False, allow_null=True)
    notes = drf_serializers.CharField(required=False, allow_blank=True, allow_null=True)


class UpdateStepInputSerializer(drf_serializers.Serializer):
    step_id = drf_serializers.IntegerField()
    location = drf_serializers.IntegerField(required=False, allow_null=True)
    order = drf_serializers.IntegerField(required=False, allow_null=True)
    planned_arrival = drf_serializers.DateTimeField(required=False, allow_null=True)
    planned_departure = drf_serializers.DateTimeField(required=False, allow_null=True)
    notes = drf_serializers.CharField(required=False, allow_blank=True, allow_null=True)


class StepIdInputSerializer(drf_serializers.Serializer):
    step_id = drf_serializers.IntegerField()


class StepEventInputSerializer(drf_serializers.Serializer):
    step_id = drf_serializers.IntegerField()
    occurred_at = drf_serializers.DateTimeField(required=False, allow_null=True)


class RouteViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        logist_only_actions = {
            'create',
            'update',
            'partial_update',
            'destroy',
            'confirm',
            'cancel',
            'generate_default_steps',
            'replace_steps',
            'add_step',
            'update_step',
            'remove_step',
        }

        driver_or_logist_actions = {
            'list',
            'retrieve',
            'start',
            'complete',
            'mark_step_arrival',
            'mark_step_departure',
        }

        if self.action in logist_only_actions:
            return [IsLogist()]

        if self.action in driver_or_logist_actions:
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
        qs = (
            Route.objects.select_related(
                'driver',
                'origin',
                'destination',
                'dispatch_group',
                'created_by',
            )
            .prefetch_related(
                'steps',
                'steps__location',
            )
            .annotate(_step_count=Count('steps'))
        )

        if user.role == Role.DRIVER:
            qs = qs.filter(driver=user)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self._detail_response(serializer.instance)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        route = self.get_object()

        if route.status not in {RouteStatus.DRAFT, RouteStatus.CANCELLED}:
            return Response(
                {'detail': 'Видаляти можна лише маршрут у статусі "Чернетка" або "Скасовано".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_destroy(route)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _detail_response(self, route, status_code=status.HTTP_200_OK):
        route.refresh_from_db()
        serializer = RouteDetailSerializer(route, context=self.get_serializer_context())
        return Response(serializer.data, status=status_code)

    def _service_error_response(self, exc):
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _get_route_step(self, route, step_id):
        step = route.steps.filter(pk=step_id).first()
        if not step:
            raise ValueError('Крок маршруту не знайдено.')
        return step

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        route = self.get_object()

        try:
            RouteService.confirm(route, confirmed_by=request.user)
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        route = self.get_object()

        try:
            RouteService.start(route, started_by=request.user, sync_dispatch=True)
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        route = self.get_object()

        try:
            RouteService.complete(route, completed_by=request.user, sync_dispatch=True)
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        route = self.get_object()

        try:
            RouteService.cancel(route, cancelled_by=request.user)
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def generate_default_steps(self, request, pk=None):
        route = self.get_object()
        serializer = GenerateStepsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RouteService.generate_default_steps(
                route=route,
                transit_location_ids=serializer.validated_data.get('transit_location_ids', []),
                replace_existing=serializer.validated_data.get('replace_existing', False),
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def replace_steps(self, request, pk=None):
        route = self.get_object()
        serializer = ReplaceStepsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RouteService.replace_steps(
                route=route,
                location_ids=serializer.validated_data['location_ids'],
                updated_by=request.user,
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def add_step(self, request, pk=None):
        route = self.get_object()
        serializer = AddStepInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RouteService.add_step(
                route=route,
                location=serializer.validated_data['location'],
                order=serializer.validated_data.get('order'),
                planned_arrival=serializer.validated_data.get('planned_arrival'),
                planned_departure=serializer.validated_data.get('planned_departure'),
                notes=serializer.validated_data.get('notes') or '',
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def update_step(self, request, pk=None):
        route = self.get_object()
        serializer = UpdateStepInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            step = self._get_route_step(route, serializer.validated_data['step_id'])
            RouteService.update_step(
                step=step,
                location=serializer.validated_data.get('location'),
                order=serializer.validated_data.get('order'),
                planned_arrival=serializer.validated_data.get('planned_arrival'),
                planned_departure=serializer.validated_data.get('planned_departure'),
                notes=serializer.validated_data.get('notes'),
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def remove_step(self, request, pk=None):
        route = self.get_object()
        serializer = StepIdInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            step = self._get_route_step(route, serializer.validated_data['step_id'])
            RouteService.remove_step(step)
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def mark_step_arrival(self, request, pk=None):
        route = self.get_object()
        serializer = StepEventInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            step = self._get_route_step(route, serializer.validated_data['step_id'])
            RouteService.mark_step_arrival(
                step=step,
                arrived_at=serializer.validated_data.get('occurred_at'),
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)

    @action(detail=True, methods=['post'])
    def mark_step_departure(self, request, pk=None):
        route = self.get_object()
        serializer = StepEventInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            step = self._get_route_step(route, serializer.validated_data['step_id'])
            RouteService.mark_step_departure(
                step=step,
                departed_at=serializer.validated_data.get('occurred_at'),
            )
        except ValueError as exc:
            return self._service_error_response(exc)

        return self._detail_response(route)