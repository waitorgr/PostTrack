from django.contrib import admin
from .models import TrackingEvent


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ("shipment", "status", "location", "created_at")
    list_filter = ("status", "location__city")
    search_fields = ("shipment__tracking_code",)
