from rest_framework.permissions import BasePermission

from .models import Role


class BaseRolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in self.allowed_roles
        )


class IsAdmin(BaseRolePermission):
    allowed_roles = (Role.ADMIN,)


class IsHR(BaseRolePermission):
    allowed_roles = (Role.HR, Role.ADMIN)


class IsPostalWorker(BaseRolePermission):
    allowed_roles = (Role.POSTAL_WORKER, Role.ADMIN)


class IsSortingCenterWorker(BaseRolePermission):
    allowed_roles = (Role.SORTING_CENTER_WORKER, Role.ADMIN)


class IsDistributionCenterWorker(BaseRolePermission):
    allowed_roles = (Role.DISTRIBUTION_CENTER_WORKER, Role.ADMIN)


class IsDriver(BaseRolePermission):
    allowed_roles = (Role.DRIVER, Role.ADMIN)


class IsLogist(BaseRolePermission):
    allowed_roles = (Role.LOGIST, Role.ADMIN)


class IsPostalOrDistributionCenterWorker(BaseRolePermission):
    allowed_roles = (
        Role.POSTAL_WORKER,
        Role.DISTRIBUTION_CENTER_WORKER,
        Role.ADMIN,
    )


class IsDriverOrLogist(BaseRolePermission):
    allowed_roles = (
        Role.DRIVER,
        Role.LOGIST,
        Role.ADMIN,
    )


class IsStaff(BaseRolePermission):
    allowed_roles = (
        Role.POSTAL_WORKER,
        Role.SORTING_CENTER_WORKER,
        Role.DISTRIBUTION_CENTER_WORKER,
        Role.DRIVER,
        Role.LOGIST,
        Role.HR,
        Role.ADMIN,
    )


# Залишено для сумісності зі старими імпортами
IsDisrributionCenterWorker = IsDistributionCenterWorker
IsPostalOrWarehouse = IsPostalOrDistributionCenterWorker


class CanViewDriversForRouting(BasePermission):
    """
    Доступ тільки до списку водіїв для задач маршрутизації.
    Не відкриває повний список працівників.
    """

    allowed_roles = {'admin', 'hr', 'logist'}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, 'is_superuser', False):
            return True

        role = getattr(user, 'role', None)
        if hasattr(role, 'value'):
            role = role.value

        return str(role).lower() in self.allowed_roles