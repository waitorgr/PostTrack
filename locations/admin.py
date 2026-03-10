from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "type", "parent_dc", "parent_sc", "city")
    list_filter = ("type", "city")
    search_fields = ("code", "name", "city", "address")
    readonly_fields = ("code", "created_at", "updated_at")
