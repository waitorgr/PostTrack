from django.contrib import admin
from .models import Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'city', 'code', 'is_active']
    list_filter = ['type', 'city']
    list_filter = ("type", "city")
    search_fields = ("name", "code")
