"""
python manage.py seed_data        — заповнити базу тестовими даними
python manage.py seed_data --clear — очистити і заповнити знову
"""
from django.core.management.base import BaseCommand
from django.db import transaction


LOCATIONS = [
    # Поштові відділення
    {'name': 'Відділення №1 Київ',   'type': 'post_office',         'city': 'Київ',    'address': 'вул. Хрещатик, 1',       'code': 'PO-KV-01'},
    {'name': 'Відділення №2 Харків',  'type': 'post_office',         'city': 'Харків',  'address': 'пр. Науки, 14',          'code': 'PO-KH-01'},
    {'name': 'Відділення №3 Львів',   'type': 'post_office',         'city': 'Львів',   'address': 'пл. Ринок, 5',           'code': 'PO-LV-01'},
    {'name': 'Відділення №4 Одеса',   'type': 'post_office',         'city': 'Одеса',   'address': 'вул. Дерибасівська, 2',  'code': 'PO-OD-01'},
    {'name': 'Відділення №5 Дніпро',  'type': 'post_office',         'city': 'Дніпро',  'address': 'пр. Дмитра Яворницького, 3', 'code': 'PO-DN-01'},
    # Сортувальні центри
    {'name': 'СЦ Київ',              'type': 'sorting_center',       'city': 'Київ',    'address': 'вул. Промислова, 10',    'code': 'SC-KV-01'},
    {'name': 'СЦ Харків',            'type': 'sorting_center',       'city': 'Харків',  'address': 'вул. Індустріальна, 7',  'code': 'SC-KH-01'},
    {'name': 'СЦ Львів',             'type': 'sorting_center',       'city': 'Львів',   'address': 'вул. Городоцька, 200',   'code': 'SC-LV-01'},
    {'name': 'СЦ Одеса',             'type': 'sorting_center',       'city': 'Одеса',   'address': 'вул. Балківська, 45',    'code': 'SC-OD-01'},
    # Розподільчі центри
    {'name': 'РЦ Київ',              'type': 'distribution_center',  'city': 'Київ',    'address': 'вул. Бориспільська, 9',  'code': 'DC-KV-01'},
    {'name': 'РЦ Харків',            'type': 'distribution_center',  'city': 'Харків',  'address': 'вул. Шевченка, 100',     'code': 'DC-KH-01'},
    {'name': 'РЦ Одеса',             'type': 'distribution_center',  'city': 'Одеса',   'address': 'вул. Овідіопольська, 3', 'code': 'DC-OD-01'},
]

WORKERS = [
    # (prefix, count, role, location_codes)
    ('PWorker', 10, 'postal_worker',    ['PO-KV-01', 'PO-KH-01', 'PO-LV-01', 'PO-OD-01', 'PO-DN-01']),
    ('SWorker', 10, 'warehouse_worker', ['SC-KV-01', 'SC-KH-01', 'SC-LV-01', 'SC-OD-01']),
    ('LWorker', 5,  'logist',           []),
    ('DWorker', 10, 'driver',           []),
    ('HWorker', 3,  'hr',               []),
]


class Command(BaseCommand):
    help = 'Заповнює базу даних тестовими даними'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Очистити всі дані перед заповненням')

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User, Role
        from locations.models import Location

        if options['clear']:
            self.stdout.write('Очищення бази...')
            User.objects.filter(is_superuser=False).delete()
            Location.objects.all().delete()

        # ── Локації ────────────────────────────────────────
        self.stdout.write('Створення локацій...')
        loc_map = {}
        for loc_data in LOCATIONS:
            loc, created = Location.objects.get_or_create(
                code=loc_data['code'],
                defaults=loc_data,
            )
            loc_map[loc_data['code']] = loc
            if created:
                self.stdout.write(f'  + {loc}')

        # ── Admin ──────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@posttrack.ua',
                password='adminadmin',
                first_name='Адмін',
                last_name='Системний',
                patronymic='Головний',
                phone='+380991234567',
                role=Role.ADMIN,
            )
            self.stdout.write('  + admin (superuser)')

        # ── Клієнти ────────────────────────────────────────
        self.stdout.write('Створення клієнтів...')
        for i in range(1, 11):
            username = f'CWorker{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'client{i}@posttrack.ua',
                    password='adminadmin',
                    first_name='Клієнт',
                    last_name=f'Тестовий{i}',
                    patronymic='Іванович',
                    phone=f'+38099000{i:04d}',
                    role=Role.CUSTOMER,
                )
                self.stdout.write(f'  + {username}')

        # ── Працівники ─────────────────────────────────────
        self.stdout.write('Створення працівників...')
        for prefix, count, role, loc_codes in WORKERS:
            for i in range(1, count + 1):
                username = f'{prefix}{i}'
                if not User.objects.filter(username=username).exists():
                    location = None
                    if loc_codes:
                        location = loc_map.get(loc_codes[(i - 1) % len(loc_codes)])
                    User.objects.create_user(
                        username=username,
                        email=f'{username.lower()}@posttrack.ua',
                        password='adminadmin',
                        first_name='Працівник',
                        last_name=f'{prefix}{i}',
                        patronymic='Тестович',
                        phone=f'+38097{i:07d}',
                        role=role,
                        location=location,
                    )
                    self.stdout.write(f'  + {username} ({role})'
                                      + (f' → {location}' if location else ''))

        self.stdout.write(self.style.SUCCESS('\n✅ Тестові дані успішно створено!'))
        self.stdout.write('\nЛогіни:  PWorker1-10, SWorker1-10, LWorker1-5, DWorker1-10, HWorker1-3, CWorker1-10, admin')
        self.stdout.write('Пароль:  adminadmin')
