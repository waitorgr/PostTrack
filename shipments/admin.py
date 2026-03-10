from django.contrib import admin
from .models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "status", "origin", "destination", "size", "price", "created_at")
    list_filter = ("status", "size", "origin__city", "destination__city")
    search_fields = ("tracking_code", "sender_name", "recipient_name", "sender_phone", "recipient_phone")
    readonly_fields = ("tracking_code", "created_at", "updated_at")
