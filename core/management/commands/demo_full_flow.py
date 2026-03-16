from pathlib import Path
from datetime import timedelta
from decimal import Decimal
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection

from accounts.models import User, Role
from locations.models import Region, City, Location, LocationType
from shipments.models import Shipment, Payment, PaymentType, ShipmentStatus
from dispatch.models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus
from logistics.models import Route, RouteStatus
from tracking.models import TrackingEvent
from reports.pdf_generator import (
    generate_shipment_receipt,
    generate_dispatch_depart_report,
    generate_dispatch_arrive_report,
    generate_delivery_report,
    generate_payment_report,
    generate_location_report,
)


class Command(BaseCommand):
    help = "Демо повного логістичного циклу з покроковим виводом і збереженням PDF-звітів"

    def handle(self, *args, **options):
        self.started_at = timezone.now()
        self.output_dir = self._prepare_output_dir()

        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("СТАРТ ДЕМО-ПОТОКУ ДОСТАВКИ"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"Звіти будуть збережені в: {self.output_dir}")
        self.stdout.write("")

        self._cleanup_demo_data()
        self._step("Очищення старих демо-даних завершено")

        self._create_locations()
        self._step("Локації створено")

        self._create_workers()
        self._step("Працівників створено")

        shipments = self._create_shipments(40)
        self._step(f"Створено {len(shipments)} посилок")

        receipt_pdf = generate_shipment_receipt(shipments[0])
        self._save_pdf("01_shipment_receipt_first.pdf", receipt_pdf)
        self._step("Звіт-квитанцію для першої посилки збережено")

        group_1 = self._create_dispatch_group(
            origin=self.origin_po,
            destination=self.origin_sc,
            driver=self.driver_leg_1,
            created_by=self.origin_po_worker,
            shipments=shipments,
        )
        route_1 = self._create_route(
            group=group_1,
            driver=self.driver_leg_1,
            created_by=self.origin_logist,
            notes="Маршрут 1: Відділення відправника -> СЦ відправника",
        )
        self._step("Створено dispatch і маршрут: PO -> SC")

        self._run_leg(
            step_prefix="02_leg_po_to_origin_sc",
            group=group_1,
            route=route_1,
            depart_actor=self.origin_po_worker,
            arrive_actor=self.origin_sc_worker,
            sort_actor=self.origin_sc_worker,
            sort_location=self.origin_sc,
            do_sort=True,
        )
        self._step("Виконано перевезення та сортування: PO -> SC")

        group_2 = self._create_dispatch_group(
            origin=self.origin_sc,
            destination=self.dest_sc,
            driver=self.driver_leg_2,
            created_by=self.intercity_logist,
            shipments=shipments,
        )
        route_2 = self._create_route(
            group=group_2,
            driver=self.driver_leg_2,
            created_by=self.intercity_logist,
            notes="Маршрут 2: СЦ відправника -> СЦ отримувача",
        )
        self._step("Створено dispatch і маршрут: SC -> SC")

        self._run_leg(
            step_prefix="03_leg_origin_sc_to_dest_sc",
            group=group_2,
            route=route_2,
            depart_actor=self.origin_sc_worker,
            arrive_actor=self.dest_sc_worker,
            sort_actor=self.dest_sc_worker,
            sort_location=self.dest_sc,
            do_sort=True,
        )
        self._step("Виконано перевезення та сортування: SC -> SC")

        group_3 = self._create_dispatch_group(
            origin=self.dest_sc,
            destination=self.dest_dc,
            driver=self.driver_leg_3,
            created_by=self.dest_logist,
            shipments=shipments,
        )
        route_3 = self._create_route(
            group=group_3,
            driver=self.driver_leg_3,
            created_by=self.dest_logist,
            notes="Маршрут 3: СЦ отримувача -> РЦ отримувача",
        )
        self._step("Створено dispatch і маршрут: SC -> DC")

        self._run_leg(
            step_prefix="04_leg_dest_sc_to_dest_dc",
            group=group_3,
            route=route_3,
            depart_actor=self.dest_sc_worker,
            arrive_actor=self.dest_dc_worker,
            sort_actor=self.dest_dc_worker,
            sort_location=self.dest_dc,
            do_sort=True,
        )
        self._step("Виконано перевезення та сортування: SC -> DC")

        group_4 = self._create_dispatch_group(
            origin=self.dest_dc,
            destination=self.dest_po,
            driver=self.driver_leg_4,
            created_by=self.dest_logist,
            shipments=shipments,
        )
        route_4 = self._create_route(
            group=group_4,
            driver=self.driver_leg_4,
            created_by=self.dest_logist,
            notes="Маршрут 4: РЦ отримувача -> Відділення отримувача",
        )
        self._step("Створено dispatch і маршрут: DC -> PO")

        self._run_leg(
            step_prefix="05_leg_dest_dc_to_dest_po",
            group=group_4,
            route=route_4,
            depart_actor=self.dest_dc_worker,
            arrive_actor=self.dest_po_worker,
            do_sort=False,
        )
        self._step("Виконано перевезення: DC -> PO")

        self._mark_available_for_pickup(
            shipments=shipments,
            actor=self.dest_po_worker,
            location=self.dest_po,
        )
        self._step("Усі посилки переведено в статус available_for_pickup")

        self._deliver_shipments(
            shipments=shipments,
            actor=self.dest_po_worker,
            location=self.dest_po,
        )
        self._step("Усі посилки видано отримувачам")

        delivery_pdf = generate_delivery_report(shipments[0], confirmed_by=self.dest_po_worker)
        payment_pdf = generate_payment_report(shipments[0])

        location_pdf_origin = generate_location_report(
            location=self.origin_po,
            shipments=list(Shipment.objects.filter(origin=self.origin_po)),
            dispatch_groups=list(DispatchGroup.objects.filter(origin=self.origin_po)),
            date_from=timezone.now() - timedelta(days=1),
            date_to=timezone.now() + timedelta(days=1),
        )
        location_pdf_dest = generate_location_report(
            location=self.dest_po,
            shipments=list(Shipment.objects.filter(destination=self.dest_po)),
            dispatch_groups=list(DispatchGroup.objects.filter(destination=self.dest_po)),
            date_from=timezone.now() - timedelta(days=1),
            date_to=timezone.now() + timedelta(days=1),
        )

        self._save_pdf("06_delivery_report_first.pdf", delivery_pdf)
        self._save_pdf("07_payment_report_first.pdf", payment_pdf)
        self._save_pdf("08_location_report_origin_po.pdf", location_pdf_origin)
        self._save_pdf("09_location_report_dest_po.pdf", location_pdf_dest)
        self._step("Фінальні звіти збережено")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("ДЕМО УСПІШНО ЗАВЕРШЕНО"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"Посилок доставлено: {Shipment.objects.filter(status=ShipmentStatus.DELIVERED).count()}")
        self.stdout.write(f"Оплат підтверджено: {Payment.objects.filter(is_paid=True).count()}")
        self.stdout.write(f"Маршрутів завершено: {Route.objects.filter(status=RouteStatus.COMPLETED).count()}")
        self.stdout.write(f"Dispatch-груп завершено: {DispatchGroup.objects.filter(status=DispatchGroupStatus.COMPLETED).count()}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Переглянути звіти можна тут: {self.output_dir}"))

    def _step(self, message):
        self.stdout.write(self.style.SUCCESS(f"[OK] {message}"))

    def _prepare_output_dir(self):
        base_dir = Path(settings.MEDIA_ROOT) / "demo_reports"
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        output_dir = base_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_pdf(self, filename, buffer):
        file_path = self.output_dir / filename
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())
        self.stdout.write(f"   -> PDF збережено: {file_path.name}")

    def _cleanup_demo_data(self):
        """
        Видаляємо тільки транзакційні демо-дані.
        Користувачів і довідники не чіпаємо, щоб не впасти на каскадах
        до apps, таблиці яких у БД ще не створені (наприклад chat).
        """

        # 1. Tracking
        if self._table_exists(TrackingEvent):
            TrackingEvent.objects.filter(
                shipment__sender_email__startswith="sender"
            ).delete()

        # 2. Payment
        if self._table_exists(Payment):
            Payment.objects.filter(
                shipment__sender_email__startswith="sender"
            ).delete()

        # 3. Route
        if self._table_exists(Route):
            Route.objects.filter(
                created_by__username__in=[
                    "origin_logist",
                    "intercity_logist",
                    "dest_logist",
                ]
            ).delete()

        # 4. Dispatch items
        if self._table_exists(DispatchGroupItem):
            DispatchGroupItem.objects.filter(
                shipment__sender_email__startswith="sender"
            ).delete()

        # 5. Dispatch groups
        if self._table_exists(DispatchGroup):
            DispatchGroup.objects.filter(
                created_by__username__in=[
                    "origin_po_worker",
                    "origin_sc_worker",
                    "dest_sc_worker",
                    "dest_dc_worker",
                    "dest_logist",
                    "origin_logist",
                    "intercity_logist",
                ]
            ).delete()

        # 6. Shipments
        if self._table_exists(Shipment):
            Shipment.objects.filter(
                sender_email__startswith="sender"
            ).delete()

    def _table_exists(self, model):
        return model._meta.db_table in connection.introspection.table_names()

    def _create_locations(self):
        self.origin_region, _ = Region.objects.update_or_create(
            code="KY",
            defaults={"name": "Київська область"},
        )
        self.dest_region, _ = Region.objects.update_or_create(
            code="LV",
            defaults={"name": "Львівська область"},
        )
    
        self.origin_city, _ = City.objects.update_or_create(
            name="Київ",
            defaults={"region": self.origin_region},
        )
        self.dest_city, _ = City.objects.update_or_create(
            name="Львів",
            defaults={"region": self.dest_region},
        )
    
        self.origin_sc, _ = Location.objects.update_or_create(
            code="10",
            defaults={
                "name": "Київ СЦ",
                "type": LocationType.SORTING_CENTER,
                "city": self.origin_city,
                "address": "Київ, вул. Сортувальна, 1",
                "parent_sc": None,
                "parent_dc": None,
                "is_active": True,
            },
        )
    
        self.origin_dc, _ = Location.objects.update_or_create(
            code="10111",
            defaults={
                "name": "Київ РЦ",
                "type": LocationType.DISTRIBUTION_CENTER,
                "city": self.origin_city,
                "address": "Київ, вул. Розподільча, 10",
                "parent_sc": self.origin_sc,
                "parent_dc": None,
                "is_active": True,
            },
        )
    
        self.origin_po, _ = Location.objects.update_or_create(
            code="1011100001",
            defaults={
                "name": "Київ Відділення №1",
                "type": LocationType.POST_OFFICE,
                "city": self.origin_city,
                "address": "Київ, вул. Поштова, 100",
                "parent_sc": None,
                "parent_dc": self.origin_dc,
                "is_active": True,
            },
        )
    
        self.dest_sc, _ = Location.objects.update_or_create(
            code="20",
            defaults={
                "name": "Львів СЦ",
                "type": LocationType.SORTING_CENTER,
                "city": self.dest_city,
                "address": "Львів, вул. Сортувальна, 1",
                "parent_sc": None,
                "parent_dc": None,
                "is_active": True,
            },
        )
    
        self.dest_dc, _ = Location.objects.update_or_create(
            code="20222",
            defaults={
                "name": "Львів РЦ",
                "type": LocationType.DISTRIBUTION_CENTER,
                "city": self.dest_city,
                "address": "Львів, вул. Розподільча, 10",
                "parent_sc": self.dest_sc,
                "parent_dc": None,
                "is_active": True,
            },
        )
    
        self.dest_po, _ = Location.objects.update_or_create(
            code="2022200005",
            defaults={
                "name": "Львів Відділення №5",
                "type": LocationType.POST_OFFICE,
                "city": self.dest_city,
                "address": "Львів, вул. Поштова, 55",
                "parent_sc": None,
                "parent_dc": self.dest_dc,
                "is_active": True,
            },
        )

    def _make_user(self, username, role, location=None, region=None):
        defaults = {
            "email": f"{username}@example.com",
            "first_name": "Тест",
            "last_name": username,
            "patronymic": "Іванович",
            "phone": "+380501234567",
            "role": role,
            "location": location,
            "region": region,
            "is_active": True,
        }

        user, created = User.objects.update_or_create(
            username=username,
            defaults=defaults,
        )
        user.set_password("TestPass123!")
        user.save(update_fields=[
            "password",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "phone",
            "role",
            "location",
            "region",
            "is_active",
        ])
        return user

    def _create_workers(self):
        self.hr = self._make_user("hr_user", Role.HR, region=self.origin_region)

        self.origin_po_worker = self._make_user("origin_po_worker", Role.POSTAL_WORKER, location=self.origin_po)
        self.origin_sc_worker = self._make_user("origin_sc_worker", Role.SORTING_CENTER_WORKER, location=self.origin_sc)
        self.dest_sc_worker = self._make_user("dest_sc_worker", Role.SORTING_CENTER_WORKER, location=self.dest_sc)
        self.dest_dc_worker = self._make_user("dest_dc_worker", Role.DISTRIBUTION_CENTER_WORKER, location=self.dest_dc)
        self.dest_po_worker = self._make_user("dest_po_worker", Role.POSTAL_WORKER, location=self.dest_po)

        self.driver_leg_1 = self._make_user("driver_leg_1", Role.DRIVER, location=self.origin_po)
        self.driver_leg_2 = self._make_user("driver_leg_2", Role.DRIVER, location=self.origin_sc)
        self.driver_leg_3 = self._make_user("driver_leg_3", Role.DRIVER, location=self.dest_sc)
        self.driver_leg_4 = self._make_user("driver_leg_4", Role.DRIVER, location=self.dest_dc)

        self.origin_logist = self._make_user("origin_logist", Role.LOGIST, region=self.origin_region)
        self.intercity_logist = self._make_user("intercity_logist", Role.LOGIST, region=self.origin_region)
        self.dest_logist = self._make_user("dest_logist", Role.LOGIST, region=self.dest_region)

    def _create_shipments(self, count):
        shipments = []

        for idx in range(count):
            shipment = Shipment.objects.create(
                sender_first_name=f"Sender{idx}",
                sender_last_name="Test",
                sender_patronymic="One",
                sender_phone="+380671111111",
                sender_email=f"sender{idx}@example.com",
                receiver_first_name=f"Receiver{idx}",
                receiver_last_name="Test",
                receiver_patronymic="Two",
                receiver_phone="+380681111111",
                receiver_email=f"receiver{idx}@example.com",
                origin=self.origin_po,
                destination=self.dest_po,
                weight=Decimal("2.50"),
                description=f"Посилка #{idx}",
                price=Shipment.calculate_price(Decimal("2.50")),
                payment_type=PaymentType.CASH_ON_DELIVERY,
                status=ShipmentStatus.ACCEPTED,
                created_by=self.origin_po_worker,
            )
            Payment.objects.create(
                shipment=shipment,
                amount=shipment.price,
                is_paid=False,
            )
            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="accepted",
                location=self.origin_po,
                created_by=self.origin_po_worker,
                note="Посилку прийнято у відділенні.",
                is_public=True,
            )
            shipments.append(shipment)

        return shipments

    def _create_dispatch_group(self, origin, destination, driver, created_by, shipments):
        group = DispatchGroup.objects.create(
            origin=origin,
            destination=destination,
            driver=driver,
            current_location=origin,
            created_by=created_by,
            status=DispatchGroupStatus.FORMING,
        )
        for shipment in shipments:
            DispatchGroupItem.objects.create(
                group=group,
                shipment=shipment,
                added_by=created_by,
            )
        group.status = DispatchGroupStatus.READY
        group.save(update_fields=["status"])
        return group

    def _create_route(self, group, driver, created_by, notes):
        return Route.objects.create(
            driver=driver,
            dispatch_group=group,
            origin=group.origin,
            destination=group.destination,
            status=RouteStatus.DRAFT,
            is_auto=True,
            scheduled_departure=timezone.now() + timedelta(hours=1),
            notes=notes,
            created_by=created_by,
        )

    def _run_leg(
        self,
        *,
        step_prefix,
        group,
        route,
        depart_actor,
        arrive_actor,
        sort_actor=None,
        sort_location=None,
        do_sort=True,
    ):
        route.status = RouteStatus.CONFIRMED
        route.save(update_fields=["status"])

        route.status = RouteStatus.IN_PROGRESS
        route.save(update_fields=["status"])

        group.status = DispatchGroupStatus.IN_TRANSIT
        group.departed_at = timezone.now()
        group.current_location = None
        group.save(update_fields=["status", "departed_at", "current_location"])

        for item in group.items.select_related("shipment"):
            shipment = item.shipment

            shipment.status = ShipmentStatus.PICKED_UP_BY_DRIVER
            shipment.save(update_fields=["status", "updated_at"])
            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="picked_up_by_driver",
                location=group.origin,
                created_by=depart_actor,
                note=f"Dispatch група {group.code} передана водію.",
                is_public=True,
            )

            shipment.status = ShipmentStatus.IN_TRANSIT
            shipment.save(update_fields=["status", "updated_at"])
            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="in_transit",
                location=group.origin,
                created_by=depart_actor,
                note=f"Відправлено з {group.origin.name} до {group.destination.name}.",
                is_public=True,
            )

        depart_pdf = generate_dispatch_depart_report(group, handed_by=depart_actor)
        self._save_pdf(f"{step_prefix}_depart.pdf", depart_pdf)

        group.status = DispatchGroupStatus.ARRIVED
        group.arrived_at = timezone.now()
        group.current_location = group.destination
        group.save(update_fields=["status", "arrived_at", "current_location"])

        for item in group.items.select_related("shipment"):
            shipment = item.shipment
            shipment.status = ShipmentStatus.ARRIVED_AT_FACILITY
            shipment.save(update_fields=["status", "updated_at"])
            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="arrived_at_facility",
                location=group.destination,
                created_by=arrive_actor,
                note=f"Прибуло до {group.destination.name}.",
                is_public=True,
            )

        arrive_pdf = generate_dispatch_arrive_report(group, received_by=arrive_actor)
        self._save_pdf(f"{step_prefix}_arrive.pdf", arrive_pdf)

        if do_sort:
            for item in group.items.select_related("shipment"):
                shipment = item.shipment
                shipment.status = ShipmentStatus.SORTED
                shipment.save(update_fields=["status", "updated_at"])
                TrackingEvent.objects.create(
                    shipment=shipment,
                    event_type="sorted",
                    location=sort_location,
                    created_by=sort_actor,
                    note=f"Відсортовано на локації {sort_location.name}.",
                    is_public=True,
                )

        route.status = RouteStatus.COMPLETED
        route.save(update_fields=["status"])

        group.status = DispatchGroupStatus.COMPLETED
        group.save(update_fields=["status"])

    def _mark_available_for_pickup(self, shipments, actor, location):
        for shipment in shipments:
            shipment.status = ShipmentStatus.AVAILABLE_FOR_PICKUP
            shipment.save(update_fields=["status", "updated_at"])
            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="available_for_pickup",
                location=location,
                created_by=actor,
                note="Посилка очікує отримання у відділенні.",
                is_public=True,
            )

    def _deliver_shipments(self, shipments, actor, location):
        for shipment in shipments:
            shipment.status = ShipmentStatus.DELIVERED
            shipment.save(update_fields=["status", "updated_at"])

            payment = shipment.payment
            if shipment.payment_type == PaymentType.CASH_ON_DELIVERY:
                payment.is_paid = True
                payment.paid_at = timezone.now()
                payment.received_by = actor
                payment.save(update_fields=["is_paid", "paid_at", "received_by"])

            TrackingEvent.objects.create(
                shipment=shipment,
                event_type="delivered",
                location=location,
                created_by=actor,
                note="Посилку видано отримувачу.",
                is_public=True,
            )