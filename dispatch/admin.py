from django.contrib import admin
from .models import DispatchGroup, DispatchGroupItem


class DispatchGroupItemInline(admin.TabularInline):
    model = DispatchGroupItem
    extra = 0


@admin.register(DispatchGroup)
class DispatchGroupAdmin(admin.ModelAdmin):
    list_display = ("group_code", "status", "from_location", "to_location", "created_at")
    list_filter = ("status", "from_location__type", "to_location__type")
    search_fields = ("group_code",)
    inlines = [DispatchGroupItemInline]
    readonly_fields = ("group_code", "created_at", "updated_at")
