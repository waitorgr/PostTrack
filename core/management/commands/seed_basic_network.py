from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Створює базову мережу: 2 регіони, 2 СЦ, 4 РЦ, 4 поштові відділення, "
        "працівників локацій, 2 логістів, водіїв і тестові посилки."
    )

    PASSWORD = "adminadmin"
    SHIPMENT_PREFIX = "[BASIC-NETWORK-SEED]"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Повністю очистити тестові посилки, користувачів seed-а та мережу перед заповненням.",
        )
        parser.add_argument(
            "--shipments-per-pair",
            type=int,
            default=2,
            help="Скільки посилок створювати на кожну пару відділень. За замовчуванням: 2",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import Role
        from locations.models import City, Location, LocationType, Region
        from shipments.models import Payment, PaymentType, Shipment, ShipmentStatus
        from tracking.utils import create_tracking_event

        User = get_user_model()

        per_pair = max(1, int(options["shipments_per_pair"]))

        network = [
            {
                "region": {"name": "Київський регіон", "code": "01"},
                "logist": {
                    "username": "logist01",
                    "email": "logist01@example.com",
                    "last_name": "Литвин",
                    "first_name": "Олена",
                    "patronymic": "Ігорівна",
                    "phone": "+380500000131",
                    "role": Role.LOGIST,
                },
                "sc": {
                    "code": "01",
                    "name": "СЦ Київ",
                    "city": "Київ",
                    "address": "м. Київ, вул. Центральна, 1",
                    "worker": {
                        "username": "sc01worker",
                        "email": "sc01worker@example.com",
                        "last_name": "Коваленко",
                        "first_name": "Іван",
                        "patronymic": "Петрович",
                        "phone": "+380500000101",
                        "role": Role.SORTING_CENTER_WORKER,
                    },
                    "driver": {
                        "username": "driver01sc",
                        "email": "driver01sc@example.com",
                        "last_name": "Данилюк",
                        "first_name": "Максим",
                        "patronymic": "Олегович",
                        "phone": "+380500000141",
                        "role": Role.DRIVER,
                    },
                },
                "dcs": [
                    {
                        "code": "01001",
                        "name": "РЦ Київ-1",
                        "city": "Бровари",
                        "address": "м. Бровари, вул. Логістична, 10",
                        "worker": {
                            "username": "dc01001worker",
                            "email": "dc01001worker@example.com",
                            "last_name": "Мельник",
                            "first_name": "Олег",
                            "patronymic": "Іванович",
                            "phone": "+380500000111",
                            "role": Role.DISTRIBUTION_CENTER_WORKER,
                        },
                        "driver": {
                            "username": "driver01001dc",
                            "email": "driver01001dc@example.com",
                            "last_name": "Черненко",
                            "first_name": "Артем",
                            "patronymic": "Юрійович",
                            "phone": "+380500000151",
                            "role": Role.DRIVER,
                        },
                        "po": {
                            "code": "0100100001",
                            "name": "Відділення Київ-1",
                            "city": "Бровари",
                            "address": "м. Бровари, вул. Поштова, 1",
                            "worker": {
                                "username": "po0100100001worker",
                                "email": "po0100100001worker@example.com",
                                "last_name": "Шевченко",
                                "first_name": "Марія",
                                "patronymic": "Олександрівна",
                                "phone": "+380500000121",
                                "role": Role.POSTAL_WORKER,
                            },
                        },
                    },
                    {
                        "code": "01002",
                        "name": "РЦ Київ-2",
                        "city": "Біла Церква",
                        "address": "м. Біла Церква, вул. Логістична, 20",
                        "worker": {
                            "username": "dc01002worker",
                            "email": "dc01002worker@example.com",
                            "last_name": "Ткаченко",
                            "first_name": "Андрій",
                            "patronymic": "Сергійович",
                            "phone": "+380500000112",
                            "role": Role.DISTRIBUTION_CENTER_WORKER,
                        },
                        "driver": {
                            "username": "driver01002dc",
                            "email": "driver01002dc@example.com",
                            "last_name": "Сидоренко",
                            "first_name": "Віталій",
                            "patronymic": "Павлович",
                            "phone": "+380500000152",
                            "role": Role.DRIVER,
                        },
                        "po": {
                            "code": "0100200001",
                            "name": "Відділення Київ-2",
                            "city": "Біла Церква",
                            "address": "м. Біла Церква, вул. Поштова, 2",
                            "worker": {
                                "username": "po0100200001worker",
                                "email": "po0100200001worker@example.com",
                                "last_name": "Бондар",
                                "first_name": "Наталія",
                                "patronymic": "Вікторівна",
                                "phone": "+380500000122",
                                "role": Role.POSTAL_WORKER,
                            },
                        },
                    },
                ],
            },
            {
                "region": {"name": "Львівський регіон", "code": "02"},
                "logist": {
                    "username": "logist02",
                    "email": "logist02@example.com",
                    "last_name": "Гуменюк",
                    "first_name": "Тарас",
                    "patronymic": "Михайлович",
                    "phone": "+380500000231",
                    "role": Role.LOGIST,
                },
                "sc": {
                    "code": "02",
                    "name": "СЦ Львів",
                    "city": "Львів",
                    "address": "м. Львів, вул. Центральна, 2",
                    "worker": {
                        "username": "sc02worker",
                        "email": "sc02worker@example.com",
                        "last_name": "Савчук",
                        "first_name": "Петро",
                        "patronymic": "Миколайович",
                        "phone": "+380500000201",
                        "role": Role.SORTING_CENTER_WORKER,
                    },
                    "driver": {
                        "username": "driver02sc",
                        "email": "driver02sc@example.com",
                        "last_name": "Шумський",
                        "first_name": "Богдан",
                        "patronymic": "Іванович",
                        "phone": "+380500000241",
                        "role": Role.DRIVER,
                    },
                },
                "dcs": [
                    {
                        "code": "02001",
                        "name": "РЦ Львів-1",
                        "city": "Дрогобич",
                        "address": "м. Дрогобич, вул. Логістична, 10",
                        "worker": {
                            "username": "dc02001worker",
                            "email": "dc02001worker@example.com",
                            "last_name": "Козак",
                            "first_name": "Роман",
                            "patronymic": "Степанович",
                            "phone": "+380500000211",
                            "role": Role.DISTRIBUTION_CENTER_WORKER,
                        },
                        "driver": {
                            "username": "driver02001dc",
                            "email": "driver02001dc@example.com",
                            "last_name": "Паламарчук",
                            "first_name": "Сергій",
                            "patronymic": "Романович",
                            "phone": "+380500000251",
                            "role": Role.DRIVER,
                        },
                        "po": {
                            "code": "0200100001",
                            "name": "Відділення Львів-1",
                            "city": "Дрогобич",
                            "address": "м. Дрогобич, вул. Поштова, 1",
                            "worker": {
                                "username": "po0200100001worker",
                                "email": "po0200100001worker@example.com",
                                "last_name": "Гнатюк",
                                "first_name": "Ірина",
                                "patronymic": "Володимирівна",
                                "phone": "+380500000221",
                                "role": Role.POSTAL_WORKER,
                            },
                        },
                    },
                    {
                        "code": "02002",
                        "name": "РЦ Львів-2",
                        "city": "Червоноград",
                        "address": "м. Червоноград, вул. Логістична, 20",
                        "worker": {
                            "username": "dc02002worker",
                            "email": "dc02002worker@example.com",
                            "last_name": "Романюк",
                            "first_name": "Юрій",
                            "patronymic": "Ігорович",
                            "phone": "+380500000212",
                            "role": Role.DISTRIBUTION_CENTER_WORKER,
                        },
                        "driver": {
                            "username": "driver02002dc",
                            "email": "driver02002dc@example.com",
                            "last_name": "Василюк",
                            "first_name": "Орест",
                            "patronymic": "Васильович",
                            "phone": "+380500000252",
                            "role": Role.DRIVER,
                        },
                        "po": {
                            "code": "0200200001",
                            "name": "Відділення Львів-2",
                            "city": "Червоноград",
                            "address": "м. Червоноград, вул. Поштова, 2",
                            "worker": {
                                "username": "po0200200001worker",
                                "email": "po0200200001worker@example.com",
                                "last_name": "Кравець",
                                "first_name": "Оксана",
                                "patronymic": "Іванівна",
                                "phone": "+380500000222",
                                "role": Role.POSTAL_WORKER,
                            },
                        },
                    },
                ],
            },
        ]

        if options["clear"]:
            self._clear_existing(User)

        created_regions = 0
        created_cities = 0
        created_locations = 0
        created_users = 0
        po_locations = []
        po_workers_by_code = {}

        for region_data in network:
            region, region_created = Region.objects.get_or_create(
                code=region_data["region"]["code"],
                defaults={"name": region_data["region"]["name"]},
            )
            if not region_created and region.name != region_data["region"]["name"]:
                region.name = region_data["region"]["name"]
                region.save(update_fields=["name"])
            created_regions += int(region_created)

            logist_user, was_created = self._upsert_user(
                User,
                username=region_data["logist"]["username"],
                password=self.PASSWORD,
                email=region_data["logist"]["email"],
                last_name=region_data["logist"]["last_name"],
                first_name=region_data["logist"]["first_name"],
                patronymic=region_data["logist"]["patronymic"],
                phone=region_data["logist"]["phone"],
                role=region_data["logist"]["role"],
                region=region,
                location=None,
                is_active=True,
            )
            created_users += int(was_created)

            sc_city, city_created = City.objects.get_or_create(name=region_data["sc"]["city"], region=region)
            created_cities += int(city_created)

            sc, sc_created = Location.objects.update_or_create(
                code=region_data["sc"]["code"],
                defaults={
                    "name": region_data["sc"]["name"],
                    "type": LocationType.SORTING_CENTER,
                    "city": sc_city,
                    "address": region_data["sc"]["address"],
                    "is_active": True,
                    "parent_sc": None,
                    "parent_dc": None,
                },
            )
            created_locations += int(sc_created)

            _, was_created = self._upsert_user(
                User,
                username=region_data["sc"]["worker"]["username"],
                password=self.PASSWORD,
                email=region_data["sc"]["worker"]["email"],
                last_name=region_data["sc"]["worker"]["last_name"],
                first_name=region_data["sc"]["worker"]["first_name"],
                patronymic=region_data["sc"]["worker"]["patronymic"],
                phone=region_data["sc"]["worker"]["phone"],
                role=region_data["sc"]["worker"]["role"],
                location=sc,
                region=None,
                is_active=True,
            )
            created_users += int(was_created)

            _, was_created = self._upsert_user(
                User,
                username=region_data["sc"]["driver"]["username"],
                password=self.PASSWORD,
                email=region_data["sc"]["driver"]["email"],
                last_name=region_data["sc"]["driver"]["last_name"],
                first_name=region_data["sc"]["driver"]["first_name"],
                patronymic=region_data["sc"]["driver"]["patronymic"],
                phone=region_data["sc"]["driver"]["phone"],
                role=region_data["sc"]["driver"]["role"],
                location=sc,
                region=None,
                is_active=True,
            )
            created_users += int(was_created)

            for dc_data in region_data["dcs"]:
                dc_city, city_created = City.objects.get_or_create(name=dc_data["city"], region=region)
                created_cities += int(city_created)

                dc, dc_created = Location.objects.update_or_create(
                    code=dc_data["code"],
                    defaults={
                        "name": dc_data["name"],
                        "type": LocationType.DISTRIBUTION_CENTER,
                        "city": dc_city,
                        "address": dc_data["address"],
                        "is_active": True,
                        "parent_sc": sc,
                        "parent_dc": None,
                    },
                )
                created_locations += int(dc_created)

                _, was_created = self._upsert_user(
                    User,
                    username=dc_data["worker"]["username"],
                    password=self.PASSWORD,
                    email=dc_data["worker"]["email"],
                    last_name=dc_data["worker"]["last_name"],
                    first_name=dc_data["worker"]["first_name"],
                    patronymic=dc_data["worker"]["patronymic"],
                    phone=dc_data["worker"]["phone"],
                    role=dc_data["worker"]["role"],
                    location=dc,
                    region=None,
                    is_active=True,
                )
                created_users += int(was_created)

                _, was_created = self._upsert_user(
                    User,
                    username=dc_data["driver"]["username"],
                    password=self.PASSWORD,
                    email=dc_data["driver"]["email"],
                    last_name=dc_data["driver"]["last_name"],
                    first_name=dc_data["driver"]["first_name"],
                    patronymic=dc_data["driver"]["patronymic"],
                    phone=dc_data["driver"]["phone"],
                    role=dc_data["driver"]["role"],
                    location=dc,
                    region=None,
                    is_active=True,
                )
                created_users += int(was_created)

                po_data = dc_data["po"]
                po_city, city_created = City.objects.get_or_create(name=po_data["city"], region=region)
                created_cities += int(city_created)

                po, po_created = Location.objects.update_or_create(
                    code=po_data["code"],
                    defaults={
                        "name": po_data["name"],
                        "type": LocationType.POST_OFFICE,
                        "city": po_city,
                        "address": po_data["address"],
                        "is_active": True,
                        "parent_sc": None,
                        "parent_dc": dc,
                    },
                )
                created_locations += int(po_created)

                po_worker, was_created = self._upsert_user(
                    User,
                    username=po_data["worker"]["username"],
                    password=self.PASSWORD,
                    email=po_data["worker"]["email"],
                    last_name=po_data["worker"]["last_name"],
                    first_name=po_data["worker"]["first_name"],
                    patronymic=po_data["worker"]["patronymic"],
                    phone=po_data["worker"]["phone"],
                    role=po_data["worker"]["role"],
                    location=po,
                    region=None,
                    is_active=True,
                )
                created_users += int(was_created)
                po_locations.append(po)
                po_workers_by_code[po.code] = po_worker

        shipments_created = self._reseed_shipments(
            Shipment=Shipment,
            Payment=Payment,
            PaymentType=PaymentType,
            ShipmentStatus=ShipmentStatus,
            create_tracking_event=create_tracking_event,
            po_locations=po_locations,
            po_workers_by_code=po_workers_by_code,
            per_pair=per_pair,
        )

        self.stdout.write(self.style.SUCCESS("Базова мережа успішно створена/оновлена."))
        self.stdout.write(f"Регіони: {Region.objects.count()}")
        self.stdout.write(f"Міста: {City.objects.count()}")
        self.stdout.write(f"Локації: {Location.objects.count()}")
        self.stdout.write(
            f"Працівники локацій: {User.objects.filter(role__in=[Role.SORTING_CENTER_WORKER, Role.DISTRIBUTION_CENTER_WORKER, Role.POSTAL_WORKER]).count()}"
        )
        self.stdout.write(f"Логісти: {User.objects.filter(role=Role.LOGIST).count()}")
        self.stdout.write(f"Водії: {User.objects.filter(role=Role.DRIVER).count()}")
        self.stdout.write(f"Посилки цього seed-а: {shipments_created}")
        self.stdout.write(
            f"Створено нових об'єктів -> регіони: {created_regions}, міста: {created_cities}, "
            f"локації: {created_locations}, користувачі: {created_users}"
        )
        self.stdout.write(f"Пароль для всіх створених користувачів: {self.PASSWORD}")

    def _clear_existing(self, User):
        from accounts.models import Role
        from locations.models import City, Location, Region
        from shipments.models import Shipment

        self.stdout.write(self.style.WARNING("Очищення seed-даних..."))
        Shipment.objects.all().delete()
        User.objects.filter(
            role__in=[
                Role.POSTAL_WORKER,
                Role.SORTING_CENTER_WORKER,
                Role.DISTRIBUTION_CENTER_WORKER,
                Role.LOGIST,
                Role.DRIVER,
            ]
        ).delete()
        Location.objects.all().delete()
        City.objects.all().delete()
        Region.objects.all().delete()

    def _upsert_user(self, User, username, password, **fields):
        user = User.objects.filter(username=username).first()
        created = user is None

        if created:
            user = User(username=username, **fields)
            user.set_password(password)
            user.save()
            return user, True

        updated = False
        for field, value in fields.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                updated = True

        if not user.check_password(password):
            user.set_password(password)
            updated = True

        if updated:
            user.save()

        return user, False

    def _reseed_shipments(
        self,
        *,
        Shipment,
        Payment,
        PaymentType,
        ShipmentStatus,
        create_tracking_event,
        po_locations,
        po_workers_by_code,
        per_pair,
    ):
        Shipment.objects.filter(description__startswith=self.SHIPMENT_PREFIX).delete()

        counter = 0
        for origin in po_locations:
            for destination in po_locations:
                if origin.id == destination.id:
                    continue

                creator = po_workers_by_code[origin.code]

                for attempt in range(1, per_pair + 1):
                    counter += 1
                    weight = Decimal("0.50") + Decimal(counter % 5)
                    payment_type = PaymentType.PREPAID if counter % 2 else PaymentType.CASH_ON_DELIVERY
                    price = Shipment.calculate_price(weight)

                    shipment = Shipment.objects.create(
                        sender_first_name=f"Відправник{counter}",
                        sender_last_name="Тестовий",
                        sender_patronymic="Іванович",
                        sender_phone=f"+38067000{counter:05d}",
                        sender_email=f"sender{counter}@example.com",
                        receiver_first_name=f"Отримувач{counter}",
                        receiver_last_name="Тестовий",
                        receiver_patronymic="Петрович",
                        receiver_phone=f"+38068000{counter:05d}",
                        receiver_email=f"receiver{counter}@example.com",
                        origin=origin,
                        destination=destination,
                        weight=weight,
                        description=(
                            f"{self.SHIPMENT_PREFIX} {origin.code} -> {destination.code}; "
                            f"посилка #{attempt} для пари"
                        ),
                        price=price,
                        payment_type=payment_type,
                        status=ShipmentStatus.ACCEPTED,
                        created_by=creator,
                    )

                    Payment.objects.create(
                        shipment=shipment,
                        amount=price,
                        is_paid=(payment_type == PaymentType.PREPAID),
                        paid_at=timezone.now() if payment_type == PaymentType.PREPAID else None,
                        received_by=None,
                    )

                    create_tracking_event(
                        shipment=shipment,
                        event_type=ShipmentStatus.ACCEPTED,
                        location=origin,
                        created_by=creator,
                        note="Посилку зареєстровано seed-командою базової мережі.",
                        is_public=True,
                    )

        return counter
