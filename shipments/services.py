from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from accounts.models import UserRole
from locations.models import LocationType
from shipments.transitions import ALLOWED_TRANSITIONS
from shipments.models import ShipmentStatus
from tracking.models import TrackingEvent


class ShipmentService:
    @staticmethod
    def _require_actor(actor_user):
        if actor_user is None:
            raise DjangoValidationError("actor_user is required for status change.")

    @staticmethod
    def _require_location(location):
        if location is None:
            raise DjangoValidationError("location is required for status change.")

    @staticmethod
    def _require_role(actor_user, allowed_roles: set):
        role = getattr(actor_user, "role", None)
        if role not in allowed_roles:
            raise DjangoValidationError(f"Role '{role}' is not allowed for this action.")

    @staticmethod
    def _require_location_type(location, allowed_types: set):
        if getattr(location, "type", None) not in allowed_types:
            raise DjangoValidationError("Invalid location type for this status change.")

    @staticmethod
    def _require_destination_location(shipment, location):
        """
        READY_FOR_PICKUP і DELIVERED можна виставляти тільки на destination Post Office.
        """
        if shipment.destination_id != getattr(location, "id", None):
            raise DjangoValidationError("This status can be set only at destination post office.")

    @staticmethod
    def _validate_actor_for_status(shipment, new_status, actor_user, location):
        """
        Рольові правила (простий, але реалістичний варіант):
        - PO події: POSTAL_WORKER/ADMIN
        - SC/DC події: WAREHOUSE_WORKER/ADMIN
        - Driver не змінює статус посилки.
        """
        ShipmentService._require_actor(actor_user)
        role = getattr(actor_user, "role", None)

        # CANCELLED — дозволяємо ADMIN, або працівнику (поки не доставлено)
        if new_status == ShipmentStatus.CANCELLED:
            if shipment.status == ShipmentStatus.DELIVERED:
                raise DjangoValidationError("Cannot cancel delivered shipment.")
            if role == UserRole.ADMIN:
                return
            if role in (UserRole.POSTAL_WORKER, UserRole.WAREHOUSE_WORKER):
                return
            raise DjangoValidationError("Only admin/worker can cancel shipment.")

        # Для всіх інших статусів потрібна локація
        ShipmentService._require_location(location)
        loc_type = getattr(location, "type", None)

        # READY_FOR_PICKUP / DELIVERED — тільки destination PO
        if new_status in {ShipmentStatus.READY_FOR_PICKUP, ShipmentStatus.DELIVERED}:
            ShipmentService._require_location_type(location, {LocationType.POST_OFFICE})
            ShipmentService._require_destination_location(shipment, location)
            ShipmentService._require_role(actor_user, {UserRole.POSTAL_WORKER, UserRole.ADMIN})
            return

        # AT_POST_OFFICE — дозволяємо як на origin, так і на destination
        if new_status == ShipmentStatus.AT_POST_OFFICE:
            ShipmentService._require_location_type(location, {LocationType.POST_OFFICE})
            ShipmentService._require_role(actor_user, {UserRole.POSTAL_WORKER, UserRole.ADMIN})

            # Важливо: AT_POST_OFFICE може бути і на старті, і на фініші
            if location.id not in (shipment.origin_id, shipment.destination_id):
                raise DjangoValidationError("AT_POST_OFFICE can be set only at origin or destination post office.")
            return

        # SC стани
        if new_status in {ShipmentStatus.AT_SORTING_CITY, ShipmentStatus.SORTED_WAITING_FOR_DISPATCH}:
            ShipmentService._require_location_type(location, {LocationType.SORTING_CITY})
            ShipmentService._require_role(actor_user, {UserRole.WAREHOUSE_WORKER, UserRole.ADMIN})
            return

        # DC стани
        if new_status in {ShipmentStatus.AT_DISTRIBUTION_CENTER, ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE}:
            ShipmentService._require_location_type(location, {LocationType.DISTRIBUTION_CENTER})
            ShipmentService._require_role(actor_user, {UserRole.WAREHOUSE_WORKER, UserRole.ADMIN})
            return

        # IN_TRANSIT_* підтверджує працівник вузла відправлення:
        if new_status in {
            ShipmentStatus.IN_TRANSIT_TO_SORTING_CITY,
            ShipmentStatus.IN_TRANSIT_TO_DISTRIBUTION_CENTER,
            ShipmentStatus.IN_TRANSIT_TO_POST_OFFICE,
        }:
            if loc_type == LocationType.POST_OFFICE:
                ShipmentService._require_role(actor_user, {UserRole.POSTAL_WORKER, UserRole.ADMIN})
            elif loc_type in (LocationType.SORTING_CITY, LocationType.DISTRIBUTION_CENTER):
                ShipmentService._require_role(actor_user, {UserRole.WAREHOUSE_WORKER, UserRole.ADMIN})
            else:
                raise DjangoValidationError("Invalid location type for transit confirmation.")
            return

        raise DjangoValidationError("No actor policy rule for this status.")

    @staticmethod
    @transaction.atomic
    def set_status(shipment, new_status, *, location=None, actor_user=None, comment=""):
        current = shipment.status

        if new_status == current:
            return shipment

        allowed_next = ALLOWED_TRANSITIONS.get(current, set())
        if new_status not in allowed_next:
            raise DjangoValidationError(f"Invalid transition: {current} -> {new_status}")

        ShipmentService._validate_actor_for_status(shipment, new_status, actor_user, location)

        TrackingEvent.objects.create(
            shipment=shipment,
            status=new_status,
            location=location,
            comment=comment,
        )

        shipment.status = new_status
        shipment.save(update_fields=["status"])
        return shipment
