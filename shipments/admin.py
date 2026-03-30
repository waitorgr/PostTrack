from django.contrib import admin

from .models import Payment, Shipment


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = ("amount", "is_paid", "paid_at", "received_by")
    readonly_fields = ()
    autocomplete_fields = ("received_by",)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "status",
        "payment_type",
        "price",
        "weight",
        "origin",
        "destination",
        "created_by",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_type",
        "origin",
        "destination",
        "created_at",
    )
    search_fields = (
        "tracking_number",
        "sender_first_name",
        "sender_last_name",
        "sender_patronymic",
        "sender_phone",
        "sender_email",
        "receiver_first_name",
        "receiver_last_name",
        "receiver_patronymic",
        "receiver_phone",
        "receiver_email",
        "origin__name",
        "destination__name",
    )
    readonly_fields = (
        "tracking_number",
        "created_at",
        "updated_at",
        "sender_full_name_admin",
        "receiver_full_name_admin",
    )
    fields = (
        "tracking_number",
        ("status", "payment_type"),
        ("origin", "destination"),
        ("weight", "price"),
        "description",
        ("sender_last_name", "sender_first_name", "sender_patronymic"),
        "sender_full_name_admin",
        ("sender_phone", "sender_email"),
        ("receiver_last_name", "receiver_first_name", "receiver_patronymic"),
        "receiver_full_name_admin",
        ("receiver_phone", "receiver_email"),
        "created_by",
        ("created_at", "updated_at"),
    )
    autocomplete_fields = ("origin", "destination", "created_by")
    list_select_related = ("origin", "destination", "created_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [PaymentInline]

    @admin.display(description="Відправник")
    def sender_full_name_admin(self, obj):
        return obj.sender_full_name

    @admin.display(description="Отримувач")
    def receiver_full_name_admin(self, obj):
        return obj.receiver_full_name


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "shipment",
        "amount",
        "is_paid",
        "paid_at",
        "received_by",
    )
    list_filter = (
        "is_paid",
        "paid_at",
    )
    search_fields = (
        "shipment__tracking_number",
        "received_by__username",
        "received_by__email",
        "received_by__phone",
        "shipment__sender_first_name",
        "shipment__sender_last_name",
        "shipment__receiver_first_name",
        "shipment__receiver_last_name",
    )
    autocomplete_fields = ("shipment", "received_by")
    list_select_related = ("shipment", "received_by")
    ordering = ("-paid_at", "-id")