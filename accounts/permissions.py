from rest_framework.permissions import BasePermission
from .models import Role


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == Role.ADMIN


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.HR, Role.ADMIN)


class IsPostalWorker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.POSTAL_WORKER, Role.ADMIN)


class IsSortingCenterWorker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.SORTING_CENTER_WORKER, Role.ADMIN)
    
class IsDisrributionCenterWorker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.DISTRIBUTION_CENTER_WORKER, Role.ADMIN)


class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.DRIVER, Role.ADMIN)


class IsLogist(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (Role.LOGIST, Role.ADMIN)


class IsPostalOrWarehouse(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            Role.POSTAL_WORKER, Role.WAREHOUSE_WORKER, Role.ADMIN
        )


class IsDriverOrLogist(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            Role.DRIVER, Role.LOGIST, Role.ADMIN
        )


class IsStaff(BasePermission):
    """Будь-який працівник (не клієнт)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role != Role.CUSTOMER
