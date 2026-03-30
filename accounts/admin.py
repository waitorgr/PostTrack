from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "full_name",
        "role",
        "location",
        "region",
        "phone",
        "email",
        "is_active",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "patronymic", "email", "phone")
    readonly_fields = ("date_joined", "last_login")

    fieldsets = UserAdmin.fieldsets + (
        ("PostTrack", {"fields": ("patronymic", "phone", "role", "location", "region")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("PostTrack", {"fields": ("first_name", "last_name", "patronymic", "email", "phone", "role", "location", "region")}),
    )