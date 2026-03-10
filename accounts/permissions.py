from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", "customer") in self.allowed_roles


class IsWorker(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", "customer") != "customer"


class IsPostWorkerOrAdmin(HasRole):
    allowed_roles = {"post_worker", "admin"}


class IsWarehouseWorkerOrAdmin(HasRole):
    allowed_roles = {"warehouse_worker", "admin"}


class IsLogisticianOrAdmin(HasRole):
    allowed_roles = {"logistician", "admin"}
