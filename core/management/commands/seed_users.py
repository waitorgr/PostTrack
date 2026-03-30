from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Створює тестових користувачів на основі вже створених локацій"

    DEFAULT_PASSWORD = "adminadmin"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Видалити всіх не-superuser користувачів перед заповненням")
        parser.add_argument("--customers", type=int, default=20, help="Кількість клієнтів")
        parser.add_argument("--postal-workers-per-po", type=int, default=1, help="Працівників відділення на одне поштове відділення")
        parser.add_argument("--sc-workers-per-sc", type=int, default=1, help="Працівників СЦ на один сортувальний центр")
        parser.add_argument("--dc-workers-per-dc", type=int, default=1, help="Працівників РЦ на один розподільчий центр")
        parser.add_argument("--drivers-per-sc", type=int, default=1, help="Водіїв на один сортувальний центр")
        parser.add_argument("--logists-per-region", type=int, default=1, help="Логістів на один регіон")
        parser.add_argument("--hr-count", type=int, default=5, help="Кількість HR")

    def _next_phone(self):
        self.phone_counter += 1
        return f"+380{self.phone_counter:09d}"

    def _user_defaults(self, *, email, first_name, last_name, patronymic, phone, role, location=None, region=None, is_staff=False, is_superuser=False):
        return {
            "email": email.lower().strip(),
            "first_name": first_name,
            "last_name": last_name,
            "patronymic": patronymic,
            "phone": phone,
            "role": role,
            "location": location,
            "region": region,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
            "is_active": True,
        }

    def _upsert_user(self, User, username, password, defaults):
        user = User.objects.filter(username=username).first()
        created = user is None

        if created:
            user = User(username=username)

        for field, value in defaults.items():
            setattr(user, field, value)

        if password:
            user.set_password(password)

        user.save()
        return user, created

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User, Role
        from locations.models import Location, LocationType, Region

        post_offices = list(
            Location.objects.filter(type=LocationType.POST_OFFICE).select_related("city", "city__region", "parent_dc")
        )
        sorting_centers = list(
            Location.objects.filter(type=LocationType.SORTING_CENTER).select_related("city", "city__region")
        )
        distribution_centers = list(
            Location.objects.filter(type=LocationType.DISTRIBUTION_CENTER).select_related("city", "city__region", "parent_sc")
        )
        regions = list(Region.objects.all())

        if not sorting_centers or not distribution_centers or not post_offices or not regions:
            raise CommandError(
                "Спочатку потрібно створити локації. Запусти: python manage.py seed_locations"
            )

        if options["clear"]:
            self.stdout.write("Очищення користувачів (крім superuser)...")
            User.objects.filter(is_superuser=False).delete()

        self.phone_counter = max(User.objects.count(), 0)

        counters = {
            "admin": 0,
            "customers": 0,
            "postal_workers": 0,
            "sc_workers": 0,
            "dc_workers": 0,
            "drivers": 0,
            "logists": 0,
            "hr": 0,
        }

        self.stdout.write("Створення користувачів...")

        admin_defaults = self._user_defaults(
            email="admin@posttrack.ua",
            first_name="Системний",
            last_name="Адміністратор",
            patronymic="Головний",
            phone=self._next_phone(),
            role=Role.ADMIN,
            location=None,
            region=None,
            is_staff=True,
            is_superuser=True,
        )
        _, created = self._upsert_user(User, "admin", self.DEFAULT_PASSWORD, admin_defaults)
        counters["admin"] += 1 if created else 0

        for i in range(1, options["customers"] + 1):
            username = f"customer{i:03d}"
            defaults = self._user_defaults(
                email=f"{username}@posttrack.ua",
                first_name="Клієнт",
                last_name=f"Тестовий{i:03d}",
                patronymic="Іванович",
                phone=self._next_phone(),
                role=Role.CUSTOMER,
                location=None,
                region=None,
            )
            _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
            counters["customers"] += 1 if created else 0

        postal_index = 1
        for location in post_offices:
            for worker_no in range(1, options["postal_workers_per_po"] + 1):
                username = f"pw_{location.code}_{worker_no}"
                defaults = self._user_defaults(
                    email=f"{username}@posttrack.ua",
                    first_name="Працівник",
                    last_name=f"Відділення_{postal_index:03d}",
                    patronymic="Тестович",
                    phone=self._next_phone(),
                    role=Role.POSTAL_WORKER,
                    location=location,
                    region=None,
                )
                _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
                counters["postal_workers"] += 1 if created else 0
                postal_index += 1

        sc_index = 1
        for location in sorting_centers:
            for worker_no in range(1, options["sc_workers_per_sc"] + 1):
                username = f"scw_{location.code}_{worker_no}"
                defaults = self._user_defaults(
                    email=f"{username}@posttrack.ua",
                    first_name="Працівник",
                    last_name=f"СЦ_{sc_index:03d}",
                    patronymic="Тестович",
                    phone=self._next_phone(),
                    role=Role.SORTING_CENTER_WORKER,
                    location=location,
                    region=None,
                )
                _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
                counters["sc_workers"] += 1 if created else 0
                sc_index += 1

        dc_index = 1
        for location in distribution_centers:
            for worker_no in range(1, options["dc_workers_per_dc"] + 1):
                username = f"dcw_{location.code}_{worker_no}"
                defaults = self._user_defaults(
                    email=f"{username}@posttrack.ua",
                    first_name="Працівник",
                    last_name=f"РЦ_{dc_index:03d}",
                    patronymic="Тестович",
                    phone=self._next_phone(),
                    role=Role.DISTRIBUTION_CENTER_WORKER,
                    location=location,
                    region=None,
                )
                _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
                counters["dc_workers"] += 1 if created else 0
                dc_index += 1

        driver_index = 1
        for location in sorting_centers:
            for driver_no in range(1, options["drivers_per_sc"] + 1):
                username = f"drv_{location.code}_{driver_no}"
                defaults = self._user_defaults(
                    email=f"{username}@posttrack.ua",
                    first_name="Водій",
                    last_name=f"Маршрутний_{driver_index:03d}",
                    patronymic="Тестович",
                    phone=self._next_phone(),
                    role=Role.DRIVER,
                    location=location,
                    region=None,
                )
                _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
                counters["drivers"] += 1 if created else 0
                driver_index += 1

        logist_index = 1
        for region in regions:
            for logist_no in range(1, options["logists_per_region"] + 1):
                username = f"log_{region.code.lower()}_{logist_no}"
                defaults = self._user_defaults(
                    email=f"{username}@posttrack.ua",
                    first_name="Логіст",
                    last_name=f"Регіональний_{logist_index:03d}",
                    patronymic="Тестович",
                    phone=self._next_phone(),
                    role=Role.LOGIST,
                    location=None,
                    region=region,
                )
                _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
                counters["logists"] += 1 if created else 0
                logist_index += 1

        for i in range(1, options["hr_count"] + 1):
            username = f"hr{i:03d}"
            defaults = self._user_defaults(
                email=f"{username}@posttrack.ua",
                first_name="HR",
                last_name=f"Менеджер_{i:03d}",
                patronymic="Тестович",
                phone=self._next_phone(),
                role=Role.HR,
                location=None,
                region=None,
            )
            _, created = self._upsert_user(User, username, self.DEFAULT_PASSWORD, defaults)
            counters["hr"] += 1 if created else 0

        self.stdout.write(self.style.SUCCESS("\n✅ Seed користувачів завершено"))
        self.stdout.write(f"Усього користувачів: {User.objects.count()}")
        self.stdout.write(
            "Створено нових: "
            f"admin={counters['admin']}, "
            f"customers={counters['customers']}, "
            f"postal_workers={counters['postal_workers']}, "
            f"sc_workers={counters['sc_workers']}, "
            f"dc_workers={counters['dc_workers']}, "
            f"drivers={counters['drivers']}, "
            f"logists={counters['logists']}, "
            f"hr={counters['hr']}"
        )
        self.stdout.write(f"Пароль для seed-користувачів: {self.DEFAULT_PASSWORD}")
