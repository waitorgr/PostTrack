from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from core.models import TimeStampedModel
from locations.models import Location, LocationType
from shipments.models import Shipment, ShipmentStatus
from tracking.models import TrackingEvent
from shipments.services import ShipmentService


class DispatchGroupStatus(models.TextChoices):
    CREATED = "created", "Created"          # наповнюємо
    SEALED = "sealed", "Sealed"             # закрита для змін
    IN_TRANSIT = "in_transit", "In transit"
    DROPPED_OFF = "dropped_off", "Dropped off"
    OPENED = "opened", "Opened"
    CANCELED = "canceled", "Canceled"


def generate_group_code(prefix: str = "GRP", length: int = 10) -> str:
    import random, string
    body = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{body}"


class DispatchGroup(TimeStampedModel):
    group_code = models.CharField(max_length=32, unique=True, editable=False)

    from_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="out_groups")
    to_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="in_groups")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_groups")

    status = models.CharField(max_length=20, choices=DispatchGroupStatus.choices, default=DispatchGroupStatus.CREATED)

    # pickup confirmations
    pickup_driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="pickup_as_driver")
    pickup_employee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="pickup_as_employee")
    pickup_at = models.DateTimeField(null=True, blank=True)

    # dropoff confirmations
    dropoff_driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="dropoff_as_driver")
    dropoff_employee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="dropoff_as_employee")
    dropoff_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.group_code:
            code = generate_group_code()
            while DispatchGroup.objects.filter(group_code=code).exists():
                code = generate_group_code()
            self.group_code = code
        super().save(*args, **kwargs)

    def clean(self):
        if self.from_location_id and self.to_location_id and self.from_location_id == self.to_location_id:
            raise ValidationError("from_location and to_location must be different.")

    def can_edit_items(self) -> bool:
        return self.status == DispatchGroupStatus.CREATED

    def seal(self):
        if not self.can_edit_items():
            raise ValidationError("Group cannot be sealed in current status.")
        if not self.items.exists():
            raise ValidationError("Cannot seal empty group.")
        self.status = DispatchGroupStatus.SEALED
        self.save(update_fields=["status"])

    # ---- статус посилки для "виїхало з ..." ----
    def _transit_status(self) -> str:
        t = self.to_location.type
        if t == LocationType.SORTING_CITY:
            return ShipmentStatus.IN_TRANSIT_TO_SORTING_CITY
        if t == LocationType.DISTRIBUTION_CENTER:
            return ShipmentStatus.IN_TRANSIT_TO_DISTRIBUTION_CENTER
        if t == LocationType.POST_OFFICE:
            return ShipmentStatus.IN_TRANSIT_TO_POST_OFFICE
        raise ValidationError("Unsupported to_location type.")

    # ---- статус посилки для "прибуло в ..." ----
    def _arrival_status(self) -> str:
        t = self.to_location.type
        if t == LocationType.SORTING_CITY:
            return ShipmentStatus.AT_SORTING_CITY
        if t == LocationType.DISTRIBUTION_CENTER:
            return ShipmentStatus.AT_DISTRIBUTION_CENTER
        if t == LocationType.POST_OFFICE:
            return ShipmentStatus.AT_POST_OFFICE
        raise ValidationError("Unsupported to_location type.")

    @transaction.atomic
    def on_pickup_fully_confirmed(self, changed_by_employee):
        """
        Статус посилки змінюється тільки в момент підтвердження працівником.
        Driver тут тільки "підпис".
        """
        if self.status not in (DispatchGroupStatus.SEALED, DispatchGroupStatus.IN_TRANSIT):
            raise ValidationError("Pickup can be confirmed only for SEALED/IN_TRANSIT group.")

        if not self.items.exists():
            raise ValidationError("Group has no items.")

        # Який статус має бути ДО відправки залежно від вузла, з якого відправляємо
        if self.from_location.type == LocationType.POST_OFFICE:
            expected_before = ShipmentStatus.AT_POST_OFFICE
        elif self.from_location.type == LocationType.SORTING_CITY:
            expected_before = ShipmentStatus.SORTED_WAITING_FOR_DISPATCH
        elif self.from_location.type == LocationType.DISTRIBUTION_CENTER:
            expected_before = ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE
        else:
            raise ValidationError("Unsupported from_location type for pickup.")

        new_status = self._transit_status()

        bad = []
        items = self.items.select_related("shipment")
        for it in items:
            st = it.shipment.status
            # дозволяємо повторний виклик (вже в transit)
            if st not in (expected_before, new_status):
                bad.append((it.shipment.tracking_code, st))

        if bad:
            sample = ", ".join([f"{code}:{st}" for code, st in bad[:5]])
            raise ValidationError(f"Some shipments have invalid status for pickup: {sample}")

        # Міняємо статус тільки тим, хто ще не у transit
        for it in items:
            sh = it.shipment
            if sh.status == new_status:
                continue
            try:
                ShipmentService.set_status(
                    sh,
                    new_status,
                    location=self.from_location,
                    actor_user=changed_by_employee,
                    comment=f"Group {self.group_code}: departed from {self.from_location.code}.",
                )
            except Exception as e:
                raise ValidationError(str(e))

        self.status = DispatchGroupStatus.IN_TRANSIT
        self.save(update_fields=["status"])


    @transaction.atomic
    def on_dropoff_fully_confirmed(self, changed_by_employee):
        if self.status not in (DispatchGroupStatus.IN_TRANSIT, DispatchGroupStatus.DROPPED_OFF):
            raise ValidationError("Dropoff can be confirmed only for IN_TRANSIT/DROPPED_OFF group.")

        if not self.items.exists():
            raise ValidationError("Group has no items.")

        expected_transit = self._transit_status()
        new_status = self._arrival_status()

        bad = []
        items = self.items.select_related("shipment")
        for it in items:
            st = it.shipment.status
            # дозволяємо повторний виклик (вже прибуло)
            if st not in (expected_transit, new_status):
                bad.append((it.shipment.tracking_code, st))

        if bad:
            sample = ", ".join([f"{code}:{st}" for code, st in bad[:5]])
            raise ValidationError(f"Some shipments have invalid status for dropoff: {sample}")

        for it in items:
            sh = it.shipment
            if sh.status == new_status:
                continue
            try:
                ShipmentService.set_status(
                    sh,
                    new_status,
                    location=self.to_location,
                    actor_user=changed_by_employee,
                    comment=f"Group {self.group_code}: arrived to {self.to_location.code}.",
                )
            except Exception as e:
                raise ValidationError(str(e))

        self.status = DispatchGroupStatus.DROPPED_OFF
        self.save(update_fields=["status"])


    @transaction.atomic
    def open_group(self):
        if self.status != DispatchGroupStatus.DROPPED_OFF:
            raise ValidationError("Group can be opened only after DROPPED_OFF.")
        self.status = DispatchGroupStatus.OPENED
        self.save(update_fields=["status"])

    @transaction.atomic
    def mark_sorted(self, employee_user):
        """
        Викликається на SC/DC працівником складу.
        На SC: AT_SORTING_CITY -> SORTED_WAITING_FOR_DISPATCH
        На DC: AT_DISTRIBUTION_CENTER -> SORTED_WAITING_FOR_POST_OFFICE
        """
        if self.to_location.type not in (LocationType.SORTING_CITY, LocationType.DISTRIBUTION_CENTER):
            raise ValidationError("Sorting is allowed only at SC/DC.")

        if self.status not in (DispatchGroupStatus.DROPPED_OFF, DispatchGroupStatus.OPENED):
            raise ValidationError("Sorting is allowed only after DROPPED_OFF/OPENED.")

        if self.to_location.type == LocationType.SORTING_CITY:
            expected_before = ShipmentStatus.AT_SORTING_CITY
            new_status = ShipmentStatus.SORTED_WAITING_FOR_DISPATCH
        else:
            expected_before = ShipmentStatus.AT_DISTRIBUTION_CENTER
            new_status = ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE

        items = self.items.select_related("shipment")
        bad = []
        for it in items:
            st = it.shipment.status
            # допускаємо повторний виклик (вже sorted)
            if st not in (expected_before, new_status):
                bad.append((it.shipment.tracking_code, st))

        if bad:
            sample = ", ".join([f"{code}:{st}" for code, st in bad[:5]])
            raise ValidationError(f"Some shipments have invalid status for sorting: {sample}")

        for it in items:
            sh = it.shipment
            if sh.status == new_status:
                continue
            try:
                ShipmentService.set_status(
                    sh,
                    new_status,
                    location=self.to_location,
                    actor_user=employee_user,
                    comment=f"Group {self.group_code}: sorted at {self.to_location.code}.",
                )
            except Exception as e:
                raise ValidationError(str(e))

            
    @transaction.atomic
    def create_next_groups_after_sort(self, created_by_employee):
        """
        Викликається на SC/DC після mark_sorted().
        Розбиває посилки по next-hop локації і створює по одній DispatchGroup на кожен напрям.
        Нові групи створюються у статусі CREATED (їх можна ще поповнювати перед seal).
        """
        current_node = self.to_location  # тут ми сортуємо (SC або DC)

        # next_hop_id -> {"loc": Location, "shipment_ids": []}
        buckets = {}

        # важливо: підтягуємо parent_sc/parent_dc, щоб build_route не стріляв зайвими запитами
        items = self.items.select_related(
            "shipment",
            "shipment__origin",
            "shipment__destination",
            "shipment__origin__parent_sc",
            "shipment__destination__parent_sc",
            "shipment__origin__parent_sc__parent_dc",
            "shipment__destination__parent_sc__parent_dc",
        )

        from dispatch.services import get_next_hop_location  # імпорт всередині, щоб не зловити цикли

        for item in items:
            sh = item.shipment
            next_loc = get_next_hop_location(sh, current_node)
            if not next_loc:
                continue  # це вже фініш або маршрут закінчився

            b = buckets.setdefault(next_loc.id, {"loc": next_loc, "shipment_ids": []})
            b["shipment_ids"].append(sh.id)

        new_groups = []
        for b in buckets.values():
            g = DispatchGroup.objects.create(
                from_location=current_node,
                to_location=b["loc"],
                created_by=created_by_employee,
            )
            DispatchGroupItem.objects.bulk_create(
                [DispatchGroupItem(group=g, shipment_id=sid) for sid in b["shipment_ids"]]
            )
            new_groups.append(g)

        return new_groups


    @transaction.atomic
    def mark_ready_for_pickup(self, employee_user):
        """
        Викликається у destination PO (працівник пошти) після OPENED:
        AT_POST_OFFICE -> READY_FOR_PICKUP (тільки якщо це destination цієї посилки)
        """
        if self.to_location.type != LocationType.POST_OFFICE:
            raise ValidationError("READY_FOR_PICKUP can be set only at Post Office.")
    
        if self.status != DispatchGroupStatus.OPENED:
            raise ValidationError("READY_FOR_PICKUP can be set only after group is OPENED.")
    
        items = self.items.select_related("shipment")
    
        bad = []
        for it in items:
            sh = it.shipment
            # якщо раптом у групі є не ті посилки — це проблема даних, краще впасти
            if sh.destination_id != self.to_location_id:
                bad.append((sh.tracking_code, "wrong_destination"))
                continue
            
            if sh.status not in (ShipmentStatus.AT_POST_OFFICE, ShipmentStatus.READY_FOR_PICKUP):
                bad.append((sh.tracking_code, sh.status))
    
        if bad:
            sample = ", ".join([f"{code}:{st}" for code, st in bad[:5]])
            raise ValidationError(f"Some shipments cannot be marked READY_FOR_PICKUP: {sample}")
    
        for it in items:
            sh = it.shipment
            if sh.status == ShipmentStatus.READY_FOR_PICKUP:
                continue
            try:
                ShipmentService.set_status(
                    sh,
                    ShipmentStatus.READY_FOR_PICKUP,
                    location=self.to_location,
                    actor_user=employee_user,
                    comment=f"Group {self.group_code}: ready for pickup at {self.to_location.code}.",
                )
            except Exception as e:
                raise ValidationError(str(e))



class DispatchGroupItem(TimeStampedModel):
    group = models.ForeignKey(DispatchGroup, on_delete=models.CASCADE, related_name="items")
    shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT, related_name="dispatch_items")

    class Meta:
        unique_together = ("group", "shipment")
