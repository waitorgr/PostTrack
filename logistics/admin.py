from django.contrib import admin
from .models import Route
@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['dispatch_group', 'driver', 'status', 'scheduled_departure']
    list_filter = ['status', 'is_auto']
