from django.db import transaction
from django.utils import timezone

from .models import (
    Payment,
    PaymentType,
    Shipment,
    ShipmentRouteStep,
    ShipmentRouteStepStatus,
    ShipmentStatus,
)
from .transitions import validate_status_transition


class ShipmentService:
    @staticmethod
    def _resolve_location(actor=None, fallback=None):
        if actor and getattr(actor, "location", None):
            return actor.location
        return fallback

    @staticmethod
    def _create_tracking_event(shipment: Shipment, event_type: str, actor=None, note: str = "", fallback_location=None):
        from tracking.utils import create_tracking_event

        create_tracking_event(
            shipment=shipment,
            event_type=event_type,
            location=ShipmentService._resolve_location(actor, fallback=fallback_location),
            created_by=actor,
            note=note,
            is_public=True,
        )

    @staticmethod
    def _set_status(shipment: Shipment, new_status: str, performed_by=None, note: str = "", fallback_location=None):
        validate_status_transition(shipment.status, new_status)

        shipment.status = new_status
        shipment.save(update_fields=["status", "updated_at"])

        ShipmentService._create_tracking_event(
            shipment=shipment,
            event_type=new_status,
            actor=performed_by,
            note=note,
            fallback_location=fallback_location,
        )

        return shipment

    @staticmethod
    def build_route_locations(origin, destination):
        if origin is None or destination is None:
            raise ValueError("Не вдалося побудувати маршрут: відсутній origin або destination.")

        route = [origin]

        origin_sc = origin.get_sorting_center() if hasattr(origin, "get_sorting_center") else None
        destination_sc = destination.get_sorting_center() if hasattr(destination, "get_sorting_center") else None
        destination_dc = destination.get_distribution_center() if hasattr(destination, "get_distribution_center") else None

        if origin_sc is None:
            raise ValueError("Для відділення-відправника не вдалося визначити сортувальний центр.")
        if destination_sc is None:
            raise ValueError("Для відділення-одержувача не вдалося визначити сортувальний центр.")

        def append_unique(location):
            if location is None:
                return
            if route[-1].id != location.id:
                route.append(location)

        # 1. Завжди йдемо з відділення у СЦ свого кластера.
        append_unique(origin_sc)

        # 2. Якщо доставка між різними СЦ, ідемо напряму в СЦ призначення.
        #    Проміжний origin DC тут не потрібен.
        if origin_sc.id != destination_sc.id:
            append_unique(destination_sc)

        # 3. Перед кінцевим відділенням завжди заходимо у РЦ одержувача,
        #    якщо він існує і ще не є поточною точкою маршруту.
        append_unique(destination_dc)

        # 4. Останній крок — відділення призначення.
        append_unique(destination)

        return route

    @staticmethod
    def create_route_steps(shipment: Shipment):
        route_locations = ShipmentService.build_route_locations(
            origin=shipment.origin,
            destination=shipment.destination,
        )

        steps = []
        now = timezone.now()
        for index, location in enumerate(route_locations):
            is_first = index == 0
            steps.append(
                ShipmentRouteStep(
                    shipment=shipment,
                    order=index,
                    location=location,
                    status=(
                        ShipmentRouteStepStatus.ACTIVE
                        if is_first
                        else ShipmentRouteStepStatus.PENDING
                    ),
                    actual_arrival_at=now if is_first else None,
                )
            )

        ShipmentRouteStep.objects.bulk_create(steps)
        return shipment.route_steps.select_related("location").order_by("order")

    @staticmethod
    def get_active_step(shipment: Shipment):
        return shipment.route_steps.select_related("location").filter(
            status=ShipmentRouteStepStatus.ACTIVE
        ).first()

    @staticmethod
    def get_next_step(shipment: Shipment):
        return shipment.route_steps.select_related("location").filter(
            status=ShipmentRouteStepStatus.PENDING
        ).order_by("order").first()

    @staticmethod
    def resolve_next_hop(shipment: Shipment, current_location=None):
        if shipment is None:
            raise ValueError("Посилку не знайдено.")

        active_step = ShipmentService.get_active_step(shipment)
        if active_step is None:
            raise ValueError("Для посилки не знайдено активний крок маршруту.")

        if current_location is not None and active_step.location_id != current_location.id:
            raise ValueError("Поточна локація працівника не відповідає активному кроку маршруту посилки.")

        next_step = ShipmentService.get_next_step(shipment)
        if next_step is None:
            return None

        return next_step.location

    @staticmethod
    @transaction.atomic
    def advance_route(shipment: Shipment, arrived_location, advanced_by=None):
        if shipment is None:
            raise ValueError("Посилку не знайдено.")
        if arrived_location is None:
            raise ValueError("Не вдалося визначити локацію прибуття.")

        active_step = ShipmentService.get_active_step(shipment)
        next_step = ShipmentService.get_next_step(shipment)

        if active_step is None:
            raise ValueError("Для посилки не знайдено активний крок маршруту.")
        if next_step is None:
            raise ValueError("У посилки немає наступного кроку маршруту.")
        if next_step.location_id != arrived_location.id:
            raise ValueError("Посилка не може прибути в цю локацію, бо вона не є наступним кроком маршруту.")

        now = timezone.now()
        active_step.status = ShipmentRouteStepStatus.DONE
        active_step.actual_departure_at = active_step.actual_departure_at or now
        active_step.save(update_fields=["status", "actual_departure_at", "updated_at"])

        next_step.status = ShipmentRouteStepStatus.ACTIVE
        next_step.actual_arrival_at = next_step.actual_arrival_at or now
        next_step.save(update_fields=["status", "actual_arrival_at", "updated_at"])

        shipment.current_location = arrived_location
        shipment.save(update_fields=["current_location", "updated_at"])

        ShipmentService._create_tracking_event(
            shipment=shipment,
            event_type=ShipmentStatus.ARRIVED_AT_FACILITY,
            actor=advanced_by,
            note=f"Посилка прибула до {getattr(arrived_location, 'name', arrived_location)}.",
            fallback_location=arrived_location,
        )

        return shipment

    @staticmethod
    @transaction.atomic
    def create_shipment(data: dict, created_by) -> Shipment:
        payload = dict(data)
        payload.pop("tracking_number", None)
        payload.pop("status", None)
        payload.pop("current_location", None)

        origin = getattr(created_by, "location", None)
        if origin is None:
            raise ValueError("У працівника, який створює посилку, не задано локацію.")

        payload["origin"] = origin
        payload["current_location"] = origin
        payload["price"] = Shipment.calculate_price(payload["weight"])
        payload["created_by"] = created_by
        payload["status"] = ShipmentStatus.ACCEPTED

        shipment = Shipment.objects.create(**payload)
        ShipmentService.create_route_steps(shipment)

        Payment.objects.create(
            shipment=shipment,
            amount=shipment.price,
            is_paid=(shipment.payment_type == PaymentType.PREPAID),
        )

        return shipment

    @staticmethod
    @transaction.atomic
    def update_status(shipment: Shipment, new_status: str, performed_by, note: str = "") -> Shipment:
        fallback_location = shipment.current_location or shipment.origin

        if new_status == ShipmentStatus.ARRIVED_AT_FACILITY:
            actor_location = getattr(performed_by, "location", None)
            shipment = ShipmentService.advance_route(
                shipment=shipment,
                arrived_location=actor_location,
                advanced_by=performed_by,
            )
            shipment.status = new_status
            shipment.save(update_fields=["status", "updated_at"])
            return shipment

        if new_status in {
            ShipmentStatus.AVAILABLE_FOR_PICKUP,
            ShipmentStatus.DELIVERED,
            ShipmentStatus.RETURNED,
        }:
            fallback_location = shipment.destination

        return ShipmentService._set_status(
            shipment=shipment,
            new_status=new_status,
            performed_by=performed_by,
            note=note,
            fallback_location=fallback_location,
        )

    @staticmethod
    @transaction.atomic
    def manual_sort(shipment: Shipment, sorted_by):
        current_location = getattr(sorted_by, "location", None)
        if current_location is None:
            raise ValueError("У працівника не задано поточну локацію.")

        if shipment.status != ShipmentStatus.ARRIVED_AT_FACILITY:
            raise ValueError("Ручне сортування можливе лише для посилки, що прибула на вузол.")

        next_hop = ShipmentService.resolve_next_hop(shipment, current_location)
        if next_hop is None:
            raise ValueError("У посилки немає наступного етапу маршруту.")

        from dispatch.services import DispatchService

        group, group_created = DispatchService.get_or_create_open_group(
            origin=current_location,
            destination=next_hop,
            created_by=sorted_by,
        )

        shipment = ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.SORTED,
            performed_by=sorted_by,
            note=(
                f"На вузлі визначено наступний етап: "
                f"{getattr(next_hop, 'name', next_hop)}. "
                f"Посилку буде додано до dispatch-групи {group.code}."
            ),
            fallback_location=current_location,
        )

        DispatchService.add_shipment(
            group=group,
            shipment=shipment,
            added_by=sorted_by,
        )

        return {
            "shipment": shipment,
            "next_hop": next_hop,
            "dispatch_group": group,
            "dispatch_group_created": group_created,
        }

    @staticmethod
    @transaction.atomic
    def cancel_shipment(shipment: Shipment, reason: str, cancelled_by) -> Shipment:
        return ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.CANCELLED,
            performed_by=cancelled_by,
            note=reason or "Посилку скасовано.",
            fallback_location=shipment.current_location or shipment.origin,
        )

    @staticmethod
    @transaction.atomic
    def initiate_return(shipment: Shipment, reason: str, initiated_by) -> Shipment:
        return ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.RETURNED,
            performed_by=initiated_by,
            note=reason or "Ініційовано повернення посилки.",
            fallback_location=shipment.current_location or shipment.destination,
        )

    @staticmethod
    @transaction.atomic
    def confirm_delivery(shipment: Shipment, confirmed_by) -> Shipment:
        ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.DELIVERED,
            performed_by=confirmed_by,
            note="Посилку доставлено отримувачу.",
            fallback_location=shipment.destination,
        )

        if shipment.payment_type == PaymentType.CASH_ON_DELIVERY:
            payment, _ = Payment.objects.get_or_create(
                shipment=shipment,
                defaults={"amount": shipment.price},
            )
            payment.is_paid = True
            payment.paid_at = timezone.now()
            payment.received_by = confirmed_by
            payment.save()

        return shipment

    @staticmethod
    @transaction.atomic
    def confirm_payment(shipment: Shipment, confirmed_by) -> Payment:
        payment, _ = Payment.objects.get_or_create(
            shipment=shipment,
            defaults={"amount": shipment.price},
        )

        if payment.is_paid:
            raise ValueError("Оплата вже підтверджена.")

        payment.is_paid = True
        payment.paid_at = timezone.now()
        payment.received_by = confirmed_by
        payment.save()
        return payment
