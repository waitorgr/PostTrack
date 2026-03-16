import random
import string
from django.utils import timezone

from .models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus
from shipments.models import ShipmentStatus
from tracking.utils import create_tracking_event


class DispatchService:
    @staticmethod
    def generate_code() -> str:
        while True:
            code = "DG-" + "".join(random.choices(string.digits, k=6))
            if not DispatchGroup.objects.filter(code=code).exists():
                return code

    @staticmethod
    def create_group(driver, origin, destination, created_by) -> DispatchGroup:
        return DispatchGroup.objects.create(
            code=DispatchService.generate_code(),
            driver=driver,
            origin=origin,
            destination=destination,
            current_location=origin,
            created_by=created_by,
            status=DispatchGroupStatus.FORMING,
        )

    @staticmethod
    def add_shipment(group: DispatchGroup, shipment, added_by):
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            raise ValueError("Додавати посилки можна лише до групи, яка ще не відправлена.")

        if shipment.status == ShipmentStatus.CANCELLED:
            raise ValueError("Неможливо додати скасоване відправлення.")

        item, created = DispatchGroupItem.objects.get_or_create(
            group=group,
            shipment=shipment,
            defaults={"added_by": added_by},
        )

        if not created:
            raise ValueError("Посилка вже додана до цієї групи.")

        return item

    @staticmethod
    def remove_shipment(group: DispatchGroup, shipment, removed_by):
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            raise ValueError("Видалення можливе лише з групи, яка ще не відправлена.")

        deleted, _ = DispatchGroupItem.objects.filter(
            group=group,
            shipment=shipment,
        ).delete()

        if not deleted:
            raise ValueError("Посилку не знайдено в цій групі.")

    @staticmethod
    def mark_ready(group: DispatchGroup, marked_by):
        if group.status != DispatchGroupStatus.FORMING:
            raise ValueError("У статус 'Готово' можна перевести лише групу, що формується.")

        if not group.items.exists():
            raise ValueError("Неможливо позначити готовою порожню групу.")

        group.status = DispatchGroupStatus.READY
        group.save(update_fields=["status"])

        return group

    @staticmethod
    def depart(group: DispatchGroup, departed_by):
        if group.status != DispatchGroupStatus.READY:
            raise ValueError("Група ще не готова до відправки.")

        if not group.items.exists():
            raise ValueError("Неможливо відправити порожню групу.")

        group.status = DispatchGroupStatus.IN_TRANSIT
        group.departed_at = timezone.now()
        group.current_location = None
        group.save(update_fields=["status", "departed_at", "current_location"])

        for item in group.items.select_related("shipment"):
            shipment = item.shipment
            shipment.status = ShipmentStatus.PICKED_UP_BY_DRIVER
            shipment.save(update_fields=["status", "updated_at"])

            create_tracking_event(
                shipment=shipment,
                event_type="picked_up_by_driver",
                location=group.origin,
                created_by=departed_by,
                note=f"Dispatch група {group.code} вирушила до {group.destination.name}.",
                is_public=True,
            )

        return group

    @staticmethod
    def arrive(group: DispatchGroup, arrived_by):
        if group.status != DispatchGroupStatus.IN_TRANSIT:
            raise ValueError("Група ще не відправлена або вже прибула.")

        group.status = DispatchGroupStatus.ARRIVED
        group.arrived_at = timezone.now()
        group.current_location = group.destination
        group.save(update_fields=["status", "arrived_at", "current_location"])

        for item in group.items.select_related("shipment"):
            shipment = item.shipment
            shipment.status = ShipmentStatus.ARRIVED_AT_FACILITY
            shipment.save(update_fields=["status", "updated_at"])

            create_tracking_event(
                shipment=shipment,
                event_type="arrived_at_facility",
                location=group.destination,
                created_by=arrived_by,
                note=f"Dispatch група {group.code} прибула до {group.destination.name}.",
                is_public=True,
            )

        return group

    @staticmethod
    def complete(group: DispatchGroup, completed_by):
        if group.status != DispatchGroupStatus.ARRIVED:
            raise ValueError("Завершити можна лише групу, яка вже прибула.")

        group.status = DispatchGroupStatus.COMPLETED
        group.save(update_fields=["status"])

        return group