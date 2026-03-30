from django.contrib import admin
from django.db.models import Count

from .models import DispatchGroup, DispatchGroupItem


class DispatchGroupItemInline(admin.TabularInline):
    model = DispatchGroupItem
    extra = 0
    raw_id_fields = ('shipment', 'added_by')
    readonly_fields = ('added_at',)
    fields = ('shipment', 'added_by', 'added_at')
    ordering = ('-added_at',)


@admin.register(DispatchGroup)
class DispatchGroupAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'status',
        'origin',
        'destination',
        'current_location',
        'driver',
        'items_count',
        'created_by',
        'created_at',
        'departed_at',
        'arrived_at',
    )
    list_filter = (
        'status',
        'origin',
        'destination',
        'current_location',
        'created_at',
        'departed_at',
        'arrived_at',
    )
    search_fields = (
        'code',
    )
    readonly_fields = (
        'code',
        'created_at',
    )
    raw_id_fields = (
        'origin',
        'destination',
        'current_location',
        'driver',
        'created_by',
    )
    inlines = [DispatchGroupItemInline]
    ordering = ('-created_at', '-id')
    list_select_related = (
        'origin',
        'destination',
        'current_location',
        'driver',
        'created_by',
    )

    fieldsets = (
        ('Основне', {
            'fields': (
                'code',
                'status',
                'origin',
                'destination',
                'current_location',
            )
        }),
        ('Відповідальні', {
            'fields': (
                'driver',
                'created_by',
            )
        }),
        ('Часові мітки', {
            'fields': (
                'created_at',
                'departed_at',
                'arrived_at',
            )
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'origin',
            'destination',
            'current_location',
            'driver',
            'created_by',
        ).annotate(_items_count=Count('items'))

    @admin.display(description='К-сть посилок', ordering='_items_count')
    def items_count(self, obj):
        return obj._items_count

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        for instance in instances:
            if isinstance(instance, DispatchGroupItem) and not instance.added_by_id and request.user.is_authenticated:
                instance.added_by = request.user
            instance.save()

        formset.save_m2m()


@admin.register(DispatchGroupItem)
class DispatchGroupItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'group',
        'shipment_label',
        'added_by',
        'added_at',
    )
    list_filter = (
        'group__status',
        'added_at',
    )
    search_fields = (
        'group__code',
    )
    raw_id_fields = (
        'group',
        'shipment',
        'added_by',
    )
    readonly_fields = (
        'added_at',
    )
    ordering = ('-added_at', '-id')
    list_select_related = (
        'group',
        'added_by',
    )

    @admin.display(description='Посилка')
    def shipment_label(self, obj):
        return getattr(obj.shipment, 'tracking_number', str(obj.shipment))

    def save_model(self, request, obj, form, change):
        if not obj.added_by_id and request.user.is_authenticated:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)