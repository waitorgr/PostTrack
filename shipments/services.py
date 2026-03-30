from django.db import transaction
from django.utils import timezone

from .models import Payment, PaymentType, Shipment, ShipmentStatus
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
    @transaction.atomic
    def create_shipment(data: dict, created_by) -> Shipment:
        """
        Створює посилку і пов'язану оплату.
    
        Важливо:
        - tracking_number генерується самою моделлю Shipment;
        - price рахується через Shipment.calculate_price(...);
        - origin береться з локації працівника, який створює посилку;
        - початковий tracking event НЕ створюється тут,
          бо його вже створює post_save signal.
        """
        payload = dict(data)
        payload.pop("tracking_number", None)
        payload.pop("status", None)
    
        origin = getattr(created_by, "location", None)
        if origin is None:
            raise ValueError("У працівника, який створює посилку, не задано локацію.")
    
        payload["origin"] = origin
        payload["price"] = Shipment.calculate_price(payload["weight"])
        payload["created_by"] = created_by
        payload["status"] = ShipmentStatus.ACCEPTED
    
        shipment = Shipment.objects.create(**payload)
    
        Payment.objects.create(
            shipment=shipment,
            amount=shipment.price,
            is_paid=(shipment.payment_type == PaymentType.PREPAID),
        )
    
        return shipment

    @staticmethod
    @transaction.atomic
    def update_status(shipment: Shipment, new_status: str, performed_by, note: str = "") -> Shipment:
        """
        Оновлює статус посилки з перевіркою дозволених переходів.
        """
        fallback_location = shipment.destination if new_status in {
            ShipmentStatus.AVAILABLE_FOR_PICKUP,
            ShipmentStatus.DELIVERED,
            ShipmentStatus.RETURNED,
        } else shipment.origin

        return ShipmentService._set_status(
            shipment=shipment,
            new_status=new_status,
            performed_by=performed_by,
            note=note,
            fallback_location=fallback_location,
        )

    @staticmethod
    @transaction.atomic
    def cancel_shipment(shipment: Shipment, reason: str, cancelled_by) -> Shipment:
        """
        Скасовує посилку через загальний механізм переходів.
        """
        return ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.CANCELLED,
            performed_by=cancelled_by,
            note=reason or "Посилку скасовано.",
            fallback_location=shipment.origin,
        )

    @staticmethod
    @transaction.atomic
    def initiate_return(shipment: Shipment, reason: str, initiated_by) -> Shipment:
        """
        Повернення можливе лише через дозволений перехід зі статусу DELIVERED.
        """
        return ShipmentService._set_status(
            shipment=shipment,
            new_status=ShipmentStatus.RETURNED,
            performed_by=initiated_by,
            note=reason or "Ініційовано повернення посилки.",
            fallback_location=shipment.destination,
        )

    @staticmethod
    @transaction.atomic
    def confirm_delivery(shipment: Shipment, confirmed_by) -> Shipment:
        """
        Підтверджує вручення посилки.
        Якщо оплата при отриманні — автоматично закриває Payment.
        """
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
        """
        Ручне підтвердження оплати.
        """
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