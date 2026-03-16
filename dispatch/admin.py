from django.contrib import admin
from .models import DispatchGroup, DispatchGroupItem
@admin.register(DispatchGroup)
class DispatchGroupAdmin(admin.ModelAdmin):
    list_display = ['code', 'status', 'origin', 'destination', 'driver', 'created_at']
    list_filter = ['status']
