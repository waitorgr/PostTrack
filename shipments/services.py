import random
from django.utils import timezone
from .models import Shipment, ShipmentStatus, Payment, PaymentType


class ShipmentService:
    @staticmethod
    def generate_tracking_number() -> str:
        """Формат: UA + 9 цифр + UA, наприклад UA123456789UA"""
        while True:
            digits = "".join(str(random.randint(0, 9)) for _ in range(9))
            number = f"UA{digits}UA"
            if not Shipment.objects.filter(tracking_number=number).exists():
                return number

    @staticmethod
    def calculate_price(weight: float) -> float:
        """Базовий тариф: 30 грн + 15 грн за кожен кг."""
        return round(30 + float(weight) * 15, 2)

    @staticmethod
    def create_shipment(data: dict, created_by) -> Shipment:
        """
        Створення посилки:
        - генерує tracking_number
        - рахує price
        - створює Payment
        - створює першу tracking-подію
        """
        from tracking.utils import create_tracking_event

        shipment = Shipment.objects.create(
            **data,
            tracking_number=ShipmentService.generate_tracking_number(),
            price=ShipmentService.calculate_price(data["weight"]),
            created_by=created_by,
            status=ShipmentStatus.ACCEPTED,
        )

        Payment.objects.create(
            shipment=shipment,
            amount=shipment.price,
            is_paid=(shipment.payment_type == PaymentType.PREPAID),
        )

        create_tracking_event(
            shipment=shipment,
            event_type="accepted",
            location=shipment.origin,
            created_by=created_by,
            note="Посилку прийнято та зареєстровано у системі.",
            is_public=True,
        )

        return shipment

    @staticmethod
    def cancel_shipment(shipment: Shipment, reason: str, cancelled_by):
        """
        Скасування посилки, якщо вона ще не в фінальному статусі.
        """
        from tracking.utils import create_tracking_event

        terminal_statuses = {
            ShipmentStatus.DELIVERED,
            ShipmentStatus.RETURNED,
            ShipmentStatus.CANCELLED,
        }

        if shipment.status in terminal_statuses:
            raise ValueError(
                f"Неможливо скасувати: статус '{shipment.get_status_display()}'."
            )

        shipment.status = ShipmentStatus.CANCELLED
        shipment.save(update_fields=["status", "updated_at"])

        create_tracking_event(
            shipment=shipment,
            event_type="cancelled",
            location=cancelled_by.location if getattr(cancelled_by, "location", None) else shipment.origin,
            created_by=cancelled_by,
            note=reason,
            is_public=True,
        )

    @staticmethod
    def initiate_return(shipment: Shipment, reason: str, initiated_by):
        """
        Спрощене повернення:
        окремої моделі ReturnOperation зараз немає,
        тому просто переводимо shipment у статус RETURNED.
        """
        from tracking.utils import create_tracking_event

        if shipment.status != ShipmentStatus.DELIVERED:
            raise ValueError("Повернення можливе лише для доставлених відправлень.")

        shipment.status = ShipmentStatus.RETURNED
        shipment.save(update_fields=["status", "updated_at"])

        create_tracking_event(
            shipment=shipment,
            event_type="returned",
            location=initiated_by.location if getattr(initiated_by, "location", None) else shipment.destination,
            created_by=initiated_by,
            note=reason,
            is_public=True,
        )

    @staticmethod
    def confirm_delivery(shipment: Shipment, confirmed_by):
        """
        Підтвердження вручення посилки.
        Якщо оплата при отриманні — одразу закриваємо Payment.
        """
        from tracking.utils import create_tracking_event

        if shipment.status not in (
            ShipmentStatus.OUT_FOR_DELIVERY,
            ShipmentStatus.AVAILABLE_FOR_PICKUP,
        ):
            raise ValueError("Підтвердження доставки неможливе для поточного статусу.")

        shipment.status = ShipmentStatus.DELIVERED
        shipment.save(update_fields=["status", "updated_at"])

        if shipment.payment_type == PaymentType.CASH_ON_DELIVERY:
            payment, _ = Payment.objects.get_or_create(
                shipment=shipment,
                defaults={"amount": shipment.price},
            )
            payment.is_paid = True
            payment.paid_at = timezone.now()
            payment.received_by = confirmed_by
            payment.save(update_fields=["is_paid", "paid_at", "received_by"])

        create_tracking_event(
            shipment=shipment,
            event_type="delivered",
            location=confirmed_by.location if getattr(confirmed_by, "location", None) else shipment.destination,
            created_by=confirmed_by,
            note="Посилку доставлено отримувачу.",
            is_public=True,
        )

    @staticmethod
    def update_status(shipment: Shipment, new_status: str, performed_by, note=""):
        """
        Базове оновлення статусу без current_location,
        бо такого поля в Shipment зараз немає.
        """
        from tracking.utils import create_tracking_event

        shipment.status = new_status
        shipment.save(update_fields=["status", "updated_at"])

        create_tracking_event(
            shipment=shipment,
            event_type=new_status,
            location=performed_by.location if getattr(performed_by, "location", None) else None,
            created_by=performed_by,
            note=note,
            is_public=True,
        )