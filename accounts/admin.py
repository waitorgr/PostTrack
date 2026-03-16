from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'role', 'location', 'is_active','region','phone']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
    ('PostTrack', {'fields': ('patronymic', 'phone', 'role', 'location', 'region')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('PostTrack', {'fields': ('first_name', 'last_name', 'patronymic', 'phone', 'role', 'location', 'region')}),
    )
