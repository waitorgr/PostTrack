from django.contrib import admin
from django.db.models import Count

from .models import Route, RouteStep


class RouteStepInline(admin.TabularInline):
    model = RouteStep
    extra = 0
    fields = (
        'order',
        'step_type',
        'location',
        'planned_arrival',
        'planned_departure',
        'actual_arrival',
        'actual_departure',
        'notes',
        'created_at',
    )
    readonly_fields = ('created_at',)
    raw_id_fields = ('location',)
    ordering = ('order', 'id')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dispatch_group',
        'driver',
        'origin',
        'destination',
        'status',
        'is_auto',
        'step_count_admin',
        'scheduled_departure',
        'created_by',
        'created_at',
    )
    list_filter = (
        'status',
        'is_auto',
        'scheduled_departure',
        'created_at',
        'origin',
        'destination',
    )
    search_fields = (
        'dispatch_group__code',
        'driver__username',
        'driver__email',
        'created_by__username',
        'created_by__email',
    )
    readonly_fields = (
        'created_at',
    )
    raw_id_fields = (
        'dispatch_group',
        'driver',
        'origin',
        'destination',
        'created_by',
    )
    inlines = [RouteStepInline]
    ordering = ('-created_at', '-id')
    list_select_related = (
        'dispatch_group',
        'driver',
        'origin',
        'destination',
        'created_by',
    )

    fieldsets = (
        ('Основне', {
            'fields': (
                'dispatch_group',
                'status',
                'is_auto',
            )
        }),
        ('Маршрут', {
            'fields': (
                'origin',
                'destination',
                'driver',
                'scheduled_departure',
            )
        }),
        ('Додатково', {
            'fields': (
                'notes',
                'created_by',
                'created_at',
            )
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'dispatch_group',
            'driver',
            'origin',
            'destination',
            'created_by',
        ).annotate(_step_count=Count('steps'))

    @admin.display(description='К-сть кроків', ordering='_step_count')
    def step_count_admin(self, obj):
        return obj._step_count

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RouteStep)
class RouteStepAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'route',
        'order',
        'step_type',
        'location',
        'is_completed',
        'planned_arrival',
        'planned_departure',
        'actual_arrival',
        'actual_departure',
        'created_at',
    )
    list_filter = (
        'step_type',
        'created_at',
        'planned_arrival',
        'planned_departure',
        'actual_arrival',
        'actual_departure',
    )
    search_fields = (
        'route__dispatch_group__code',
        'location__code',
        'location__name',
        'location__title',
    )
    readonly_fields = (
        'created_at',
        'is_completed',
    )
    raw_id_fields = (
        'route',
        'location',
    )
    ordering = ('route', 'order', 'id')
    list_select_related = (
        'route',
        'location',
    )

    fieldsets = (
        ('Основне', {
            'fields': (
                'route',
                'order',
                'step_type',
                'location',
            )
        }),
        ('Планові дані', {
            'fields': (
                'planned_arrival',
                'planned_departure',
            )
        }),
        ('Фактичні дані', {
            'fields': (
                'actual_arrival',
                'actual_departure',
            )
        }),
        ('Додатково', {
            'fields': (
                'notes',
                'is_completed',
                'created_at',
            )
        }),
    )