from pathlib import Path
from datetime import timedelta
from decimal import Decimal
from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import NOT_PROVIDED
from django.utils import timezone
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = "Демо повного логістичного циклу з покроковим виводом і збереженням PDF-звітів"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=40,
            help="Кількість демо-посилок (default: 40)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистити старі демо-транзакції перед запуском",
        )
        parser.add_argument(
            "--skip-reports",
            action="store_true",
            help="Не генерувати PDF-звіти",
        )

    

    # -------------------------------------------------------------------------
    # Завантаження моделей / генераторів
    # -------------------------------------------------------------------------

    def _load_models(self):
        from accounts.models import User, Role
        from locations.models import Region, City, Location, LocationType
        from shipments.models import Shipment

        self.User = User
        self.Role = Role
        self.Region = Region
        self.City = City
        self.Location = Location
        self.LocationType = LocationType
        self.Shipment = Shipment

        try:
            shipments_models = import_module("shipments.models")
            self.Payment = getattr(shipments_models, "Payment", None)
            self.PaymentType = getattr(shipments_models, "PaymentType", None)
            self.ShipmentStatus = getattr(shipments_models, "ShipmentStatus", None)
        except Exception:
            self.Payment = None
            self.PaymentType = None
            self.ShipmentStatus = None

        try:
            dispatch_models = import_module("dispatch.models")
            self.DispatchGroup = getattr(dispatch_models, "DispatchGroup")
            self.DispatchGroupItem = getattr(dispatch_models, "DispatchGroupItem", None)
            self.DispatchGroupStatus = getattr(dispatch_models, "DispatchGroupStatus", None)
        except Exception as exc:
            raise CommandError(f"Не вдалося імпортувати dispatch.models: {exc}")

        try:
            logistics_models = import_module("logistics.models")
            self.Route = getattr(logistics_models, "Route", None)
            self.RouteStatus = getattr(logistics_models, "RouteStatus", None)
        except Exception:
            self.Route = None
            self.RouteStatus = None

        try:
            tracking_models = import_module("tracking.models")
            self.TrackingEvent = getattr(tracking_models, "TrackingEvent", None)
        except Exception:
            self.TrackingEvent = None

        try:
            tracking_services = import_module("tracking.services")
            self.create_tracking_event_service = getattr(tracking_services, "create_tracking_event", None)
        except Exception:
            self.create_tracking_event_service = None

    def _load_report_generators(self):
        self.report_generators = {}

        if self.skip_reports:
            self.stdout.write(self.style.WARNING("PDF-генерація вимкнена через --skip-reports"))
            return

        try:
            pdf = import_module("reports.pdf_generator")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Не вдалося імпортувати reports.pdf_generator: {exc}"))
            return

        names = [
            "generate_shipment_receipt",
            "generate_dispatch_depart_report",
            "generate_dispatch_arrive_report",
            "generate_delivery_report",
            "generate_payment_report",
            "generate_location_report",
        ]
        for name in names:
            self.report_generators[name] = getattr(pdf, name, None)

    # -------------------------------------------------------------------------
    # Базові утиліти
    # -------------------------------------------------------------------------

    def _step(self, message):
        self.stdout.write(self.style.SUCCESS(f"[OK] {message}"))

    def _warn(self, message):
        self.stdout.write(self.style.WARNING(f"[WARN] {message}"))

    def _prepare_output_dir(self):
        base_dir = Path(settings.MEDIA_ROOT) / "demo_reports"
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        output_dir = base_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_pdf(self, filename, buffer):
        if not buffer:
            return
        file_path = self.output_dir / filename
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())
        self.stdout.write(f"   -> PDF збережено: {file_path.name}")

    def _maybe_generate_and_save(self, generator_name, filename, *args, **kwargs):
        func = self.report_generators.get(generator_name)
        if not func:
            self._warn(f"Генератор {generator_name} не знайдено, пропускаю {filename}")
            return
        try:
            buffer = func(*args, **kwargs)
            self._save_pdf(filename, buffer)
        except Exception as exc:
            self._warn(f"Не вдалося згенерувати {filename}: {exc}")

    def _table_exists(self, model):
        if not model:
            return False
        return model._meta.db_table in connection.introspection.table_names()

    def _model_has_field(self, model, field_name):
        try:
            model._meta.get_field(field_name)
            return True
        except Exception:
            return False

    def _save_instance(self, obj, *field_names):
        existing = [name for name in field_names if self._model_has_field(obj.__class__, name)]
        if existing:
            obj.save(update_fields=existing)
        else:
            obj.save()

    def _enum_value(self, enum_cls, *candidate_names, required=False, default=None):
        if not enum_cls:
            return default
        for name in candidate_names:
            if hasattr(enum_cls, name):
                member = getattr(enum_cls, name)
                return getattr(member, "value", member)
        if required:
            raise CommandError(
                f"Не знайдено жодного enum-значення серед {candidate_names} у {enum_cls.__name__}"
            )
        return default

    def _choice_value(self, model, field_name, *preferred_values):
        if not model or not self._model_has_field(model, field_name):
            return preferred_values[0] if preferred_values else None

        field = model._meta.get_field(field_name)
        choices = list(getattr(field, "choices", []) or [])
        if not choices:
            return preferred_values[0] if preferred_values else None

        choice_values = [value for value, _label in choices]

        for preferred in preferred_values:
            if preferred in choice_values:
                return preferred

        normalized = {str(v).lower(): v for v in choice_values}
        for preferred in preferred_values:
            if str(preferred).lower() in normalized:
                return normalized[str(preferred).lower()]

        return choice_values[0]

    def _fill_required_fields(self, model, payload, seed, context=None):
        context = context or {}

        for field in model._meta.fields:
            if field.auto_created or field.primary_key:
                continue
            if field.name in payload:
                continue
            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                continue
            if field.null:
                continue
            if field.default is not NOT_PROVIDED:
                continue

            # choices
            if getattr(field, "choices", None):
                payload[field.name] = list(field.choices)[0][0]
                continue

            internal_type = field.get_internal_type()

            if internal_type in {"CharField", "SlugField"}:
                if field.name == "tracking_number":
                    payload[field.name] = self._generate_tracking_number(seed)
                elif getattr(field, "unique", False):
                    payload[field.name] = f"{field.name}_{seed}_{timezone.now().strftime('%H%M%S%f')}"[: field.max_length]
                else:
                    payload[field.name] = f"{field.name}_{seed}"[: field.max_length]
                continue

            if internal_type == "TextField":
                payload[field.name] = f"demo_{seed}"
                continue

            if internal_type == "EmailField":
                payload[field.name] = f"demo.{seed}@example.com"
                continue

            if internal_type in {"DecimalField", "FloatField"}:
                payload[field.name] = Decimal("1.00")
                continue

            if internal_type in {
                "IntegerField",
                "BigIntegerField",
                "SmallIntegerField",
                "PositiveIntegerField",
                "PositiveSmallIntegerField",
            }:
                payload[field.name] = 1
                continue

            if internal_type == "BooleanField":
                payload[field.name] = False
                continue

            if internal_type == "DateTimeField":
                payload[field.name] = timezone.now()
                continue

            if internal_type == "DateField":
                payload[field.name] = timezone.localdate()
                continue

            if internal_type == "DurationField":
                payload[field.name] = timedelta()
                continue

            if internal_type == "ForeignKey":
                if field.name in context:
                    payload[field.name] = context[field.name]
                    continue

                # деякі поширені здогадки
                guesses = {
                    "origin": getattr(self, "origin_po", None),
                    "destination": getattr(self, "dest_po", None),
                    "current_location": getattr(self, "origin_po", None),
                    "location": getattr(self, "origin_po", None),
                    "city": getattr(self, "origin_city", None),
                    "region": getattr(self, "origin_region", None),
                    "created_by": getattr(self, "origin_po_worker", None),
                    "updated_by": getattr(self, "origin_po_worker", None),
                    "added_by": getattr(self, "origin_po_worker", None),
                    "received_by": getattr(self, "dest_po_worker", None),
                    "driver": getattr(self, "driver_leg_1", None),
                }
                if field.name in guesses and guesses[field.name] is not None:
                    payload[field.name] = guesses[field.name]
                    continue

                raise CommandError(
                    f"Не можу автоматично заповнити обов'язковий FK {model.__name__}.{field.name}"
                )

    def _create_instance(self, model, payload, seed, context=None):
        self._fill_required_fields(model, payload, seed=seed, context=context or {})
        return model.objects.create(**payload)

    # -------------------------------------------------------------------------
    # Очистка демо-даних
    # -------------------------------------------------------------------------

    def _cleanup_demo_data(self):
        demo_usernames = [
            "demo_hr_user",
            "demo_origin_po_worker",
            "demo_origin_sc_worker",
            "demo_dest_sc_worker",
            "demo_dest_dc_worker",
            "demo_dest_po_worker",
            "demo_driver_leg_1",
            "demo_driver_leg_2",
            "demo_driver_leg_3",
            "demo_driver_leg_4",
            "demo_origin_logist",
            "demo_intercity_logist",
            "demo_dest_logist",
        ]

        if self._table_exists(self.TrackingEvent) and self._model_has_field(self.TrackingEvent, "shipment"):
            try:
                self.TrackingEvent.objects.filter(
                    shipment__sender_email__startswith="demo.sender."
                ).delete()
            except Exception:
                pass

        if self._table_exists(self.Payment):
            try:
                self.Payment.objects.filter(
                    shipment__sender_email__startswith="demo.sender."
                ).delete()
            except Exception:
                pass

        if self._table_exists(self.Route):
            try:
                if self._model_has_field(self.Route, "created_by"):
                    self.Route.objects.filter(created_by__username__in=demo_usernames).delete()
            except Exception:
                pass

        if self._table_exists(self.DispatchGroupItem):
            try:
                if self._model_has_field(self.DispatchGroupItem, "shipment"):
                    self.DispatchGroupItem.objects.filter(
                        shipment__sender_email__startswith="demo.sender."
                    ).delete()
            except Exception:
                pass

        if self._table_exists(self.DispatchGroup):
            try:
                if self._model_has_field(self.DispatchGroup, "created_by"):
                    self.DispatchGroup.objects.filter(created_by__username__in=demo_usernames).delete()
            except Exception:
                pass

        if self._table_exists(self.Shipment):
            try:
                self.Shipment.objects.filter(sender_email__startswith="demo.sender.").delete()
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Створення локацій
    # -------------------------------------------------------------------------

    def _create_locations(self):
        self.origin_region, _ = self.Region.objects.update_or_create(
            code="KY",
            defaults={"name": "Київська область"},
        )
        self.dest_region, _ = self.Region.objects.update_or_create(
            code="LV",
            defaults={"name": "Львівська область"},
        )

        self.origin_city, _ = self.City.objects.update_or_create(
            name="Київ",
            defaults={"region": self.origin_region},
        )
        self.dest_city, _ = self.City.objects.update_or_create(
            name="Львів",
            defaults={"region": self.dest_region},
        )

        self.origin_sc, _ = self.Location.objects.update_or_create(
            code="01",
            defaults={
                "name": "Київ СЦ",
                "type": self.LocationType.SORTING_CENTER,
                "city": self.origin_city,
                "address": "Київ, вул. Сортувальна, 1",
                "parent_sc": None,
                "parent_dc": None,
                "is_active": True,
            },
        )

        self.origin_dc, _ = self.Location.objects.update_or_create(
            code="01001",
            defaults={
                "name": "Київ РЦ",
                "type": self.LocationType.DISTRIBUTION_CENTER,
                "city": self.origin_city,
                "address": "Київ, вул. Розподільча, 10",
                "parent_sc": self.origin_sc,
                "parent_dc": None,
                "is_active": True,
            },
        )

        self.origin_po, _ = self.Location.objects.update_or_create(
            code="0100100001",
            defaults={
                "name": "Київ Відділення №1",
                "type": self.LocationType.POST_OFFICE,
                "city": self.origin_city,
                "address": "Київ, вул. Поштова, 100",
                "parent_sc": None,
                "parent_dc": self.origin_dc,
                "is_active": True,
            },
        )

        self.dest_sc, _ = self.Location.objects.update_or_create(
            code="20",
            defaults={
                "name": "Львів СЦ",
                "type": self.LocationType.SORTING_CENTER,
                "city": self.dest_city,
                "address": "Львів, вул. Сортувальна, 1",
                "parent_sc": None,
                "parent_dc": None,
                "is_active": True,
            },
        )

        self.dest_dc, _ = self.Location.objects.update_or_create(
            code="20222",
            defaults={
                "name": "Львів РЦ",
                "type": self.LocationType.DISTRIBUTION_CENTER,
                "city": self.dest_city,
                "address": "Львів, вул. Розподільча, 10",
                "parent_sc": self.dest_sc,
                "parent_dc": None,
                "is_active": True,
            },
        )

        self.dest_po, _ = self.Location.objects.update_or_create(
            code="2022200005",
            defaults={
                "name": "Львів Відділення №5",
                "type": self.LocationType.POST_OFFICE,
                "city": self.dest_city,
                "address": "Львів, вул. Поштова, 55",
                "parent_sc": None,
                "parent_dc": self.dest_dc,
                "is_active": True,
            },
        )

    # -------------------------------------------------------------------------
    # Створення користувачів
    # -------------------------------------------------------------------------

    def _make_user(self, username, role_candidates, location=None, region=None):
        role_value = self._enum_value(self.Role, *role_candidates, required=True)

        defaults = {
            "email": f"{username}@example.com",
            "first_name": "Тест",
            "last_name": username,
            "password": make_password("TestPass123!"),
            "role": role_value,
            "is_active": True,
        }

        if self._model_has_field(self.User, "patronymic"):
            defaults["patronymic"] = "Іванович"

        if self._model_has_field(self.User, "phone"):
            phone_map = {
                "demo_hr_user": "+380501111111",
                "demo_origin_po_worker": "+380501111112",
                "demo_origin_sc_worker": "+380501111113",
                "demo_dest_sc_worker": "+380501111114",
                "demo_dest_dc_worker": "+380501111115",
                "demo_dest_po_worker": "+380501111116",
                "demo_driver_leg_1": "+380501111117",
                "demo_driver_leg_2": "+380501111118",
                "demo_driver_leg_3": "+380501111119",
                "demo_driver_leg_4": "+380501111120",
                "demo_origin_logist": "+380501111121",
                "demo_intercity_logist": "+380501111122",
                "demo_dest_logist": "+380501111123",
            }
            defaults["phone"] = phone_map.get(username, "+380501234567")

        if self._model_has_field(self.User, "location") and location is not None:
            defaults["location"] = location

        if self._model_has_field(self.User, "region") and region is not None:
            # HR у твоїй моделі не повинен мати region
            if role_value != self._enum_value(self.Role, "HR", required=False):
                defaults["region"] = region

        user, _ = self.User.objects.update_or_create(
            username=username,
            defaults=defaults,
        )

        return user

    def _create_workers(self):
        self.hr = self._make_user(
            "demo_hr_user",
            ["HR"],
            
        )

        self.origin_po_worker = self._make_user(
            "demo_origin_po_worker",
            ["POSTAL_WORKER", "POST_WORKER"],
            location=self.origin_po,
        )
        self.origin_sc_worker = self._make_user(
            "demo_origin_sc_worker",
            ["SORTING_CENTER_WORKER", "WAREHOUSE_WORKER", "POSTAL_WORKER"],
            location=self.origin_sc,
        )
        self.dest_sc_worker = self._make_user(
            "demo_dest_sc_worker",
            ["SORTING_CENTER_WORKER", "WAREHOUSE_WORKER", "POSTAL_WORKER"],
            location=self.dest_sc,
        )
        self.dest_dc_worker = self._make_user(
            "demo_dest_dc_worker",
            ["DISTRIBUTION_CENTER_WORKER", "WAREHOUSE_WORKER", "POSTAL_WORKER"],
            location=self.dest_dc,
        )
        self.dest_po_worker = self._make_user(
            "demo_dest_po_worker",
            ["POSTAL_WORKER", "POST_WORKER"],
            location=self.dest_po,
        )

        self.driver_leg_1 = self._make_user(
            "demo_driver_leg_1",
            ["DRIVER"],
            location=self.origin_po,
        )
        self.driver_leg_2 = self._make_user(
            "demo_driver_leg_2",
            ["DRIVER"],
            location=self.origin_sc,
        )
        self.driver_leg_3 = self._make_user(
            "demo_driver_leg_3",
            ["DRIVER"],
            location=self.dest_sc,
        )
        self.driver_leg_4 = self._make_user(
            "demo_driver_leg_4",
            ["DRIVER"],
            location=self.dest_dc,
        )

        self.origin_logist = self._make_user(
            "demo_origin_logist",
            ["LOGIST", "LOGISTICIAN"],
            region=self.origin_region,
        )
        self.intercity_logist = self._make_user(
            "demo_intercity_logist",
            ["LOGIST", "LOGISTICIAN"],
            region=self.origin_region,
        )
        self.dest_logist = self._make_user(
            "demo_dest_logist",
            ["LOGIST", "LOGISTICIAN"],
            region=self.dest_region,
        )
        self.origin_dc_worker = self._make_user(
        "demo_origin_dc_worker",
        ["DISTRIBUTION_CENTER_WORKER", "WAREHOUSE_WORKER", "POSTAL_WORKER"],
        location=self.origin_dc,
        )
        self.driver_leg_5 = self._make_user(
        "demo_driver_leg_5",
        ["DRIVER"],
        location=self.dest_dc,
        )

    # -------------------------------------------------------------------------
    # Посилки / платежі / трекінг
    # -------------------------------------------------------------------------

    def _generate_tracking_number(self, idx):
        # Формат: DEMO + timestamp + індекс, щоб уникати UNIQUE-конфліктів
        return f"DEMO{timezone.now().strftime('%y%m%d%H%M%S')}{int(idx):04d}"

    def _shipment_price(self, weight):
        if hasattr(self.Shipment, "calculate_price"):
            try:
                return self.Shipment.calculate_price(weight)
            except Exception:
                pass
        return Decimal("100.00")

    def _payment_type_cod_value(self):
        return self._enum_value(
            self.PaymentType,
            "CASH_ON_DELIVERY",
            "RECIPIENT_PAYS",
            "RECEIVER_PAYS",
            required=False,
            default=None,
        )

    def _shipment_status_value(self, *names):
        return self._enum_value(self.ShipmentStatus, *names, required=False, default=None)

    def _dispatch_status_value(self, *names):
        return self._enum_value(self.DispatchGroupStatus, *names, required=False, default=None)

    def _route_status_value(self, *names):
        return self._enum_value(self.RouteStatus, *names, required=False, default=None)

    def _set_shipment_status(self, shipment, *names):
        value = self._shipment_status_value(*names)
        if value is None or not self._model_has_field(self.Shipment, "status"):
            return
        shipment.status = value
        update_fields = ["status"]
        if self._model_has_field(self.Shipment, "updated_at"):
            update_fields.append("updated_at")
        shipment.save(update_fields=update_fields)

    def _set_group_status(self, group, *names):
        value = self._dispatch_status_value(*names)
        if value is None or not self._model_has_field(self.DispatchGroup, "status"):
            return
        group.status = value
        self._save_instance(group, "status")

    def _set_route_status(self, route, *names):
        if not route or not self.Route or not self._model_has_field(self.Route, "status"):
            return
        value = self._route_status_value(*names)
        if value is None:
            return
        route.status = value
        self._save_instance(route, "status")

    def _create_shipments(self, count):
        shipments = []
        cod_value = self._payment_type_cod_value()

        for idx in range(count):
            payload = {}

            # Контакти відправника
            for key, value in {
                "sender_first_name": f"DemoSender{idx}",
                "sender_last_name": "Test",
                "sender_patronymic": "One",
                "sender_phone": f"+380671110{idx:04d}"[:13],
                "sender_email": f"demo.sender.{idx}@example.com",
            }.items():
                if self._model_has_field(self.Shipment, key):
                    payload[key] = value

            # Контакти отримувача
            for key, value in {
                "receiver_first_name": f"DemoReceiver{idx}",
                "receiver_last_name": "Test",
                "receiver_patronymic": "Two",
                "receiver_phone": f"+380681110{idx:04d}"[:13],
                "receiver_email": f"demo.receiver.{idx}@example.com",
            }.items():
                if self._model_has_field(self.Shipment, key):
                    payload[key] = value

            # Базові поля
            weight = Decimal("2.50")
            price = self._shipment_price(weight)

            field_map = {
                "origin": self.origin_po,
                "destination": self.dest_po,
                "current_location": self.origin_po,
                "weight": weight,
                "description": f"Демо-посилка #{idx}",
                "price": price,
                "shipping_cost": price,
                "declared_value": price,
                "created_by": self.origin_po_worker,
                "tracking_number": self._generate_tracking_number(idx),
            }

            for key, value in field_map.items():
                if self._model_has_field(self.Shipment, key):
                    payload[key] = value

            if self._model_has_field(self.Shipment, "payment_type") and cod_value is not None:
                payload["payment_type"] = cod_value

            accepted_status = self._shipment_status_value("ACCEPTED", "PENDING", "CREATED")
            if self._model_has_field(self.Shipment, "status") and accepted_status is not None:
                payload["status"] = accepted_status

            shipment = self._create_instance(
                self.Shipment,
                payload,
                seed=idx,
                context={
                    "origin": self.origin_po,
                    "destination": self.dest_po,
                    "current_location": self.origin_po,
                    "created_by": self.origin_po_worker,
                },
            )

            self._create_payment_if_needed(shipment, idx)
            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["accepted", "created", "registered"],
                location=self.origin_po,
                created_by=self.origin_po_worker,
                note="Посилку прийнято у відділенні.",
                is_public=True,
            )

            shipments.append(shipment)

        return shipments

    def _create_payment_if_needed(self, shipment, idx):
        if not self.Payment or not self._table_exists(self.Payment):
            return

        payload = {}
        context = {"shipment": shipment, "received_by": self.dest_po_worker}

        if self._model_has_field(self.Payment, "shipment"):
            payload["shipment"] = shipment

        amount_value = getattr(shipment, "price", None) or getattr(shipment, "shipping_cost", None) or Decimal("100.00")
        if self._model_has_field(self.Payment, "amount"):
            payload["amount"] = amount_value
        if self._model_has_field(self.Payment, "is_paid"):
            payload["is_paid"] = False

        try:
            self._create_instance(self.Payment, payload, seed=f"payment_{idx}", context=context)
        except Exception as exc:
            self._warn(f"Не вдалося створити Payment для shipment #{shipment.pk}: {exc}")

    def _create_tracking_event(self, shipment, preferred_event_types, location=None, created_by=None, note="", is_public=True):
        if not self.TrackingEvent or not self._table_exists(self.TrackingEvent):
            return None

        event_type = self._choice_value(self.TrackingEvent, "event_type", *preferred_event_types)

        if self.create_tracking_event_service:
            try:
                return self.create_tracking_event_service(
                    shipment=shipment,
                    event_type=event_type,
                    location=location,
                    created_by=created_by,
                    note=note,
                    is_public=is_public,
                )
            except Exception:
                # fallback нижче
                pass

        payload = {}
        context = {
            "shipment": shipment,
            "location": location or self.origin_po,
            "created_by": created_by or self.origin_po_worker,
        }

        if self._model_has_field(self.TrackingEvent, "shipment"):
            payload["shipment"] = shipment
        if self._model_has_field(self.TrackingEvent, "event_type"):
            payload["event_type"] = event_type
        if self._model_has_field(self.TrackingEvent, "location"):
            payload["location"] = location
        if self._model_has_field(self.TrackingEvent, "created_by"):
            payload["created_by"] = created_by
        if self._model_has_field(self.TrackingEvent, "note"):
            payload["note"] = note
        if self._model_has_field(self.TrackingEvent, "is_public"):
            payload["is_public"] = is_public
        if self._model_has_field(self.TrackingEvent, "created_at"):
            payload["created_at"] = timezone.now()

        try:
            return self._create_instance(
                self.TrackingEvent,
                payload,
                seed=f"track_{shipment.pk}",
                context=context,
            )
        except Exception as exc:
            self._warn(f"Не вдалося створити TrackingEvent для shipment #{shipment.pk}: {exc}")
            return None

    # -------------------------------------------------------------------------
    # Dispatch / Route
    # -------------------------------------------------------------------------

    def _create_dispatch_group(self, origin, destination, driver, created_by, shipments):
        payload = {}
        context = {
            "origin": origin,
            "destination": destination,
            "current_location": origin,
            "created_by": created_by,
            "driver": driver,
        }

        for key, value in {
            "origin": origin,
            "destination": destination,
            "driver": driver,
            "current_location": origin,
            "created_by": created_by,
        }.items():
            if self._model_has_field(self.DispatchGroup, key):
                payload[key] = value

        forming_status = self._dispatch_status_value("FORMING", "DRAFT", "PLANNED", "CREATED")
        if self._model_has_field(self.DispatchGroup, "status") and forming_status is not None:
            payload["status"] = forming_status

        group = self._create_instance(
            self.DispatchGroup,
            payload,
            seed=f"group_{timezone.now().timestamp()}",
            context=context,
        )

        self._attach_shipments_to_group(group, shipments, created_by)
        self._group_shipments_map[group.pk] = shipments

        ready_status = self._dispatch_status_value("READY", "SEALED", "PLANNED")
        if ready_status is not None and self._model_has_field(self.DispatchGroup, "status"):
            group.status = ready_status
            self._save_instance(group, "status")

        return group

    def _attach_shipments_to_group(self, group, shipments, actor):
        # Варіант 1: через DispatchGroupItem
        if self.DispatchGroupItem and self._table_exists(self.DispatchGroupItem):
            for shipment in shipments:
                payload = {}
                context = {
                    "shipment": shipment,
                    "group": group,
                    "dispatch_group": group,
                    "added_by": actor,
                    "created_by": actor,
                }

                if self._model_has_field(self.DispatchGroupItem, "group"):
                    payload["group"] = group
                if self._model_has_field(self.DispatchGroupItem, "dispatch_group"):
                    payload["dispatch_group"] = group
                if self._model_has_field(self.DispatchGroupItem, "shipment"):
                    payload["shipment"] = shipment
                if self._model_has_field(self.DispatchGroupItem, "added_by"):
                    payload["added_by"] = actor
                if self._model_has_field(self.DispatchGroupItem, "created_by"):
                    payload["created_by"] = actor

                try:
                    self._create_instance(
                        self.DispatchGroupItem,
                        payload,
                        seed=f"group_item_{group.pk}_{shipment.pk}",
                        context=context,
                    )
                except Exception as exc:
                    self._warn(f"Не вдалося додати shipment #{shipment.pk} у group #{group.pk}: {exc}")
            return

        # Варіант 2: через M2M
        if hasattr(group, "shipments"):
            try:
                group.shipments.add(*shipments)
                return
            except Exception as exc:
                self._warn(f"Не вдалося додати shipments у M2M group.shipments: {exc}")

    def _create_route(self, group, driver, created_by, notes):
        if not self.Route:
            self._warn("Модель Route не знайдено, маршрут буде пропущено")
            return None

        payload = {}
        context = {
            "driver": driver,
            "created_by": created_by,
            "origin": getattr(group, "origin", self.origin_po),
            "destination": getattr(group, "destination", self.dest_po),
            "dispatch_group": group,
            "group": group,
        }

        if self._model_has_field(self.Route, "driver"):
            payload["driver"] = driver
        if self._model_has_field(self.Route, "created_by"):
            payload["created_by"] = created_by
        if self._model_has_field(self.Route, "origin"):
            payload["origin"] = getattr(group, "origin", self.origin_po)
        if self._model_has_field(self.Route, "destination"):
            payload["destination"] = getattr(group, "destination", self.dest_po)
        if self._model_has_field(self.Route, "dispatch_group"):
            payload["dispatch_group"] = group
        if self._model_has_field(self.Route, "group"):
            payload["group"] = group
        if self._model_has_field(self.Route, "notes"):
            payload["notes"] = notes
        if self._model_has_field(self.Route, "is_auto"):
            payload["is_auto"] = True
        if self._model_has_field(self.Route, "scheduled_departure"):
            payload["scheduled_departure"] = timezone.now() + timedelta(hours=1)

        draft_status = self._route_status_value("DRAFT", "PLANNED", "CREATED")
        if self._model_has_field(self.Route, "status") and draft_status is not None:
            payload["status"] = draft_status

        try:
            return self._create_instance(
                self.Route,
                payload,
                seed=f"route_{group.pk}",
                context=context,
            )
        except Exception as exc:
            self._warn(f"Не вдалося створити Route для group #{group.pk}: {exc}")
            return None

    def _shipments_from_group(self, group, fallback_shipments):
        # через related_name='items'
        if hasattr(group, "items"):
            try:
                return [item.shipment for item in group.items.select_related("shipment")]
            except Exception:
                pass

        # через M2M
        if hasattr(group, "shipments"):
            try:
                return list(group.shipments.all())
            except Exception:
                pass

        return list(self._group_shipments_map.get(group.pk, fallback_shipments or []))

    def _shipment_status_for_destination(self, destination):
        dest_type = getattr(destination, "type", None)

        if dest_type == getattr(self.LocationType, "SORTING_CENTER", None):
            return (
                self._shipment_status_value(
                    "AT_SORTING_CENTER",
                    "AT_SORTING_CITY",
                    "ARRIVED_AT_FACILITY",
                )
                or self._shipment_status_value("IN_TRANSIT")
            )

        if dest_type == getattr(self.LocationType, "DISTRIBUTION_CENTER", None):
            return (
                self._shipment_status_value(
                    "AT_DISTRIBUTION_CENTER",
                    "ARRIVED_AT_FACILITY",
                )
                or self._shipment_status_value("IN_TRANSIT")
            )

        if dest_type == getattr(self.LocationType, "POST_OFFICE", None):
            return (
                self._shipment_status_value(
                    "AT_POST_OFFICE",
                    "READY_FOR_PICKUP",
                    "AVAILABLE_FOR_PICKUP",
                )
                or self._shipment_status_value("IN_TRANSIT")
            )

        return self._shipment_status_value("IN_TRANSIT")

    def _sorted_status_for_destination(self, destination):
        dest_type = getattr(destination, "type", None)

        if dest_type == getattr(self.LocationType, "SORTING_CENTER", None):
            return self._shipment_status_value(
                "SORTED_WAITING_FOR_DISPATCH",
                "SORTED",
            )

        if dest_type == getattr(self.LocationType, "DISTRIBUTION_CENTER", None):
            return self._shipment_status_value(
                "SORTED_WAITING_FOR_POST_OFFICE",
                "SORTED",
            )

        return self._shipment_status_value("SORTED")

    def _available_for_pickup_status(self):
        return self._shipment_status_value(
            "AVAILABLE_FOR_PICKUP",
            "READY_FOR_PICKUP",
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
        fallback_shipments=None,
    ):
        if route:
            self._set_route_status(route, "CONFIRMED", "PLANNED")
            self._set_route_status(route, "IN_PROGRESS")

        if self._model_has_field(self.DispatchGroup, "status"):
            in_transit = self._dispatch_status_value("IN_TRANSIT", "DISPATCHED")
            if in_transit is not None:
                group.status = in_transit

        if self._model_has_field(self.DispatchGroup, "departed_at"):
            group.departed_at = timezone.now()
        if self._model_has_field(self.DispatchGroup, "current_location"):
            group.current_location = None

        self._save_instance(group, "status", "departed_at", "current_location")

        group_shipments = self._shipments_from_group(group, fallback_shipments)

        for shipment in group_shipments:
            self._set_shipment_status(shipment, "PICKED_UP_BY_DRIVER", "IN_TRANSIT")
            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["picked_up_by_driver", "picked_up", "in_transit"],
                location=getattr(group, "origin", None),
                created_by=depart_actor,
                note=f"Dispatch-група #{group.pk} передана водію.",
                is_public=True,
            )

            self._set_shipment_status(shipment, "IN_TRANSIT")
            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["in_transit", "departed"],
                location=getattr(group, "origin", None),
                created_by=depart_actor,
                note=f"Відправлено з {getattr(group, 'origin', 'origin')} до {getattr(group, 'destination', 'destination')}.",
                is_public=True,
            )

        self._maybe_generate_and_save(
            "generate_dispatch_depart_report",
            f"{step_prefix}_depart.pdf",
            group,
            handed_by=depart_actor,
        )

        if self._model_has_field(self.DispatchGroup, "status"):
            arrived = self._dispatch_status_value("ARRIVED", "COMPLETED")
            if arrived is not None:
                group.status = arrived
        if self._model_has_field(self.DispatchGroup, "arrived_at"):
            group.arrived_at = timezone.now()
        if self._model_has_field(self.DispatchGroup, "current_location"):
            group.current_location = getattr(group, "destination", None)

        self._save_instance(group, "status", "arrived_at", "current_location")

        for shipment in group_shipments:
            dest_status = self._shipment_status_for_destination(getattr(group, "destination", None))
            if dest_status is not None and self._model_has_field(self.Shipment, "status"):
                shipment.status = dest_status
                fields = ["status"]
                if self._model_has_field(self.Shipment, "updated_at"):
                    fields.append("updated_at")
                shipment.save(update_fields=fields)

            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["arrived_at_facility", "arrived", "received"],
                location=getattr(group, "destination", None),
                created_by=arrive_actor,
                note=f"Прибуло до {getattr(getattr(group, 'destination', None), 'name', 'локації')}.",
                is_public=True,
            )

        self._maybe_generate_and_save(
            "generate_dispatch_arrive_report",
            f"{step_prefix}_arrive.pdf",
            group,
            received_by=arrive_actor,
        )

        if do_sort:
            sorted_status = self._sorted_status_for_destination(getattr(group, "destination", None))
            for shipment in group_shipments:
                if sorted_status is not None and self._model_has_field(self.Shipment, "status"):
                    shipment.status = sorted_status
                    fields = ["status"]
                    if self._model_has_field(self.Shipment, "updated_at"):
                        fields.append("updated_at")
                    shipment.save(update_fields=fields)

                self._create_tracking_event(
                    shipment=shipment,
                    preferred_event_types=["sorted", "processed"],
                    location=sort_location,
                    created_by=sort_actor,
                    note=f"Відсортовано на локації {getattr(sort_location, 'name', 'unknown')}.",
                    is_public=True,
                )

        if route:
            self._set_route_status(route, "COMPLETED")

        self._set_group_status(group, "COMPLETED")

    # -------------------------------------------------------------------------
    # Фінальні статуси
    # -------------------------------------------------------------------------

    def _mark_available_for_pickup(self, shipments, actor, location):
        status_value = self._available_for_pickup_status()
        for shipment in shipments:
            if status_value is not None and self._model_has_field(self.Shipment, "status"):
                shipment.status = status_value
                fields = ["status"]
                if self._model_has_field(self.Shipment, "updated_at"):
                    fields.append("updated_at")
                shipment.save(update_fields=fields)

            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["available_for_pickup", "ready_for_pickup", "arrived_at_post_office"],
                location=location,
                created_by=actor,
                note="Посилка очікує отримання у відділенні.",
                is_public=True,
            )

    def _deliver_shipments(self, shipments, actor, location):
        delivered_status = self._shipment_status_value("DELIVERED", "COMPLETED")

        for shipment in shipments:
            if delivered_status is not None and self._model_has_field(self.Shipment, "status"):
                shipment.status = delivered_status
                fields = ["status"]
                if self._model_has_field(self.Shipment, "updated_at"):
                    fields.append("updated_at")
                shipment.save(update_fields=fields)

            self._mark_payment_paid_if_needed(shipment, actor)

            self._create_tracking_event(
                shipment=shipment,
                preferred_event_types=["delivered", "issued_to_receiver", "completed"],
                location=location,
                created_by=actor,
                note="Посилку видано отримувачу.",
                is_public=True,
            )

    def _mark_payment_paid_if_needed(self, shipment, actor):
        if not self.Payment or not hasattr(shipment, "payment"):
            return

        try:
            payment = shipment.payment
        except Exception:
            return

        if self._model_has_field(self.Payment, "is_paid"):
            payment.is_paid = True
        if self._model_has_field(self.Payment, "paid_at"):
            payment.paid_at = timezone.now()
        if self._model_has_field(self.Payment, "received_by"):
            payment.received_by = actor

        self._save_instance(payment, "is_paid", "paid_at", "received_by")

    # -------------------------------------------------------------------------
    # Підрахунки
    # -------------------------------------------------------------------------

    def _delivered_count(self, shipments):
        if self._model_has_field(self.Shipment, "status"):
            delivered_status = self._shipment_status_value("DELIVERED", "COMPLETED")
            if delivered_status is not None:
                return self.Shipment.objects.filter(status=delivered_status).count()
        return len(shipments)

    def _paid_count(self, shipments):
        if not self.Payment or not self._model_has_field(self.Payment, "is_paid"):
            return 0
        try:
            return self.Payment.objects.filter(is_paid=True).count()
        except Exception:
            return 0

    def _completed_routes_count(self):
        if not self.Route or not self._model_has_field(self.Route, "status"):
            return 0
        completed = self._route_status_value("COMPLETED")
        if completed is None:
            return 0
        try:
            return self.Route.objects.filter(status=completed).count()
        except Exception:
            return 0

    def _completed_dispatch_count(self):
        if not self._model_has_field(self.DispatchGroup, "status"):
            return 0
        completed = self._dispatch_status_value("COMPLETED")
        if completed is None:
            return 0
        try:
            return self.DispatchGroup.objects.filter(status=completed).count()
        except Exception:
            return 0