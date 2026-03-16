from django.contrib import admin
from .models import Shipment, Payment
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'status', 'origin', 'destination', 'weight', 'created_at']
    list_filter = ['status']
    search_fields = ['tracking_number']
