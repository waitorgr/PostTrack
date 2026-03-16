from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

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


class FullDeliveryFlowE2ETest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # ----------------------------
        # Географія
        # ----------------------------
        cls.origin_region = Region.objects.create(name="Київська область", code="KY")
        cls.dest_region = Region.objects.create(name="Львівська область", code="LV")

        cls.origin_city = City.objects.create(name="Київ", region=cls.origin_region)
        cls.dest_city = City.objects.create(name="Львів", region=cls.dest_region)

        cls.origin_sc = Location.objects.create(
            name="Київ СЦ",
            type=LocationType.SORTING_CENTER,
            city=cls.origin_city,
            address="Київ, вул. Сортувальна, 1",
            code="10",
        )
        cls.origin_dc = Location.objects.create(
            name="Київ РЦ",
            type=LocationType.DISTRIBUTION_CENTER,
            city=cls.origin_city,
            address="Київ, вул. Розподільча, 10",
            code="10111",
            parent_sc=cls.origin_sc,
        )
        cls.origin_po = Location.objects.create(
            name="Київ Відділення №1",
            type=LocationType.POST_OFFICE,
            city=cls.origin_city,
            address="Київ, вул. Поштова, 100",
            code="1011100001",
            parent_dc=cls.origin_dc,
        )

        cls.dest_sc = Location.objects.create(
            name="Львів СЦ",
            type=LocationType.SORTING_CENTER,
            city=cls.dest_city,
            address="Львів, вул. Сортувальна, 1",
            code="20",
        )
        cls.dest_dc = Location.objects.create(
            name="Львів РЦ",
            type=LocationType.DISTRIBUTION_CENTER,
            city=cls.dest_city,
            address="Львів, вул. Розподільча, 10",
            code="20222",
            parent_sc=cls.dest_sc,
        )
        cls.dest_po = Location.objects.create(
            name="Львів Відділення №5",
            type=LocationType.POST_OFFICE,
            city=cls.dest_city,
            address="Львів, вул. Поштова, 55",
            code="2022200005",
            parent_dc=cls.dest_dc,
        )

        # ----------------------------
        # Працівники
        # ----------------------------
        cls.hr = cls._make_user("hr_user", Role.HR, region=cls.origin_region)

        cls.origin_po_worker = cls._make_user(
            "origin_po_worker", Role.POSTAL_WORKER, location=cls.origin_po
        )
        cls.origin_sc_worker = cls._make_user(
            "origin_sc_worker", Role.SORTING_CENTER_WORKER, location=cls.origin_sc
        )
        cls.dest_sc_worker = cls._make_user(
            "dest_sc_worker", Role.SORTING_CENTER_WORKER, location=cls.dest_sc
        )
        cls.dest_dc_worker = cls._make_user(
            "dest_dc_worker", Role.DISTRIBUTION_CENTER_WORKER, location=cls.dest_dc
        )
        cls.dest_po_worker = cls._make_user(
            "dest_po_worker", Role.POSTAL_WORKER, location=cls.dest_po
        )

        cls.driver_leg_1 = cls._make_user(
            "driver_leg_1", Role.DRIVER, location=cls.origin_po
        )
        cls.driver_leg_2 = cls._make_user(
            "driver_leg_2", Role.DRIVER, location=cls.origin_sc
        )
        cls.driver_leg_3 = cls._make_user(
            "driver_leg_3", Role.DRIVER, location=cls.dest_sc
        )
        cls.driver_leg_4 = cls._make_user(
            "driver_leg_4", Role.DRIVER, location=cls.dest_dc
        )

        cls.origin_logist = cls._make_user(
            "origin_logist", Role.LOGIST, region=cls.origin_region
        )
        cls.intercity_logist = cls._make_user(
            "intercity_logist", Role.LOGIST, region=cls.origin_region
        )
        cls.dest_logist = cls._make_user(
            "dest_logist", Role.LOGIST, region=cls.dest_region
        )

    @classmethod
    def _make_user(cls, username, role, location=None, region=None):
        return User.objects.create_user(
            username=username,
            password="TestPass123!",
            email=f"{username}@example.com",
            first_name="Тест",
            last_name=username,
            patronymic="Іванович",
            phone="+380501234567",
            role=role,
            location=location,
            region=region,
        )

    def _assert_pdf(self, buffer):
        data = buffer.getvalue()
        self.assertTrue(data.startswith(b"%PDF"), "Файл не схожий на PDF")
        self.assertGreater(len(data), 800, "PDF підозріло малий")

    def _create_shipment(self, idx: int) -> Shipment:
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
        return shipment

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

        return depart_pdf, arrive_pdf

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

    def test_full_delivery_flow_for_40_shipments_with_reports(self):
        # 1. Працівники створені
        self.assertEqual(User.objects.exclude(role=Role.CUSTOMER).count(), 13)

        # 2. Створення 40 посилок з однаковим місцем призначення
        shipments = [self._create_shipment(i) for i in range(40)]
        self.assertEqual(len(shipments), 40)
        self.assertEqual(
            Shipment.objects.filter(destination=self.dest_po).count(),
            40,
        )

        # Звіт прийому хоча б для однієї посилки
        receipt_pdf = generate_shipment_receipt(shipments[0])
        self._assert_pdf(receipt_pdf)

        # 3-6. Dispatch 1: origin PO -> origin SC
        group_1 = self._create_dispatch_group(
            origin=self.origin_po,
            destination=self.origin_sc,
            driver=self.driver_leg_1,
            created_by=self.origin_po_worker,
            shipments=shipments,
        )
        self.assertEqual(group_1.items.count(), 40)

        route_1 = self._create_route(
            group=group_1,
            driver=self.driver_leg_1,
            created_by=self.origin_logist,
            notes="Маршрут 1: Відділення відправника -> СЦ відправника",
        )

        depart_pdf_1, arrive_pdf_1 = self._run_leg(
            group=group_1,
            route=route_1,
            depart_actor=self.origin_po_worker,
            arrive_actor=self.origin_sc_worker,
            sort_actor=self.origin_sc_worker,
            sort_location=self.origin_sc,
            do_sort=True,
        )
        self._assert_pdf(depart_pdf_1)
        self._assert_pdf(arrive_pdf_1)

        # 7-8. Dispatch 2: origin SC -> destination SC
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

        depart_pdf_2, arrive_pdf_2 = self._run_leg(
            group=group_2,
            route=route_2,
            depart_actor=self.origin_sc_worker,
            arrive_actor=self.dest_sc_worker,
            sort_actor=self.dest_sc_worker,
            sort_location=self.dest_sc,
            do_sort=True,
        )
        self._assert_pdf(depart_pdf_2)
        self._assert_pdf(arrive_pdf_2)

        # 9-10. Dispatch 3: destination SC -> destination DC
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

        depart_pdf_3, arrive_pdf_3 = self._run_leg(
            group=group_3,
            route=route_3,
            depart_actor=self.dest_sc_worker,
            arrive_actor=self.dest_dc_worker,
            sort_actor=self.dest_dc_worker,
            sort_location=self.dest_dc,
            do_sort=True,
        )
        self._assert_pdf(depart_pdf_3)
        self._assert_pdf(arrive_pdf_3)

        # 11-12. Dispatch 4: destination DC -> destination PO
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

        depart_pdf_4, arrive_pdf_4 = self._run_leg(
            group=group_4,
            route=route_4,
            depart_actor=self.dest_dc_worker,
            arrive_actor=self.dest_po_worker,
            do_sort=False,
        )
        self._assert_pdf(depart_pdf_4)
        self._assert_pdf(arrive_pdf_4)

        # 13. Готово до видачі
        self._mark_available_for_pickup(
            shipments=shipments,
            actor=self.dest_po_worker,
            location=self.dest_po,
        )
        self.assertEqual(
            Shipment.objects.filter(status=ShipmentStatus.AVAILABLE_FOR_PICKUP).count(),
            40,
        )

        # 14. Видача отримувачу
        self._deliver_shipments(
            shipments=shipments,
            actor=self.dest_po_worker,
            location=self.dest_po,
        )

        self.assertEqual(
            Shipment.objects.filter(status=ShipmentStatus.DELIVERED).count(),
            40,
        )
        self.assertEqual(
            Payment.objects.filter(is_paid=True).count(),
            40,
        )
        self.assertEqual(
            Route.objects.filter(status=RouteStatus.COMPLETED).count(),
            4,
        )
        self.assertEqual(
            DispatchGroup.objects.filter(status=DispatchGroupStatus.COMPLETED).count(),
            4,
        )

        # 15. Звіти після доставки
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

        self._assert_pdf(delivery_pdf)
        self._assert_pdf(payment_pdf)
        self._assert_pdf(location_pdf_origin)
        self._assert_pdf(location_pdf_dest)

        # 16. Перевірка трекінгу для однієї посилки
        first_shipment = shipments[0]
        event_types = list(
            TrackingEvent.objects.filter(shipment=first_shipment)
            .order_by("created_at")
            .values_list("event_type", flat=True)
        )

        self.assertIn("accepted", event_types)
        self.assertIn("picked_up_by_driver", event_types)
        self.assertIn("in_transit", event_types)
        self.assertIn("arrived_at_facility", event_types)
        self.assertIn("sorted", event_types)
        self.assertIn("available_for_pickup", event_types)
        self.assertIn("delivered", event_types)

        self.assertEqual(first_shipment.payment.is_paid, True)