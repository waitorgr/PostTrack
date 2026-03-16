from django.contrib import admin
from .models import TrackingEvent
@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'event_type', 'location', 'created_at']
    list_filter = ['event_type', 'is_public']
