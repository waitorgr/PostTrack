from decimal import Decimal
import random
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from django.utils import timezone


class Command(BaseCommand):
    help = 'Створює тестові посилки між поштовими відділеннями'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Скільки посилок створити')
        parser.add_argument('--clear', action='store_true', help='Очистити посилки перед створенням')
        parser.add_argument('--seed', type=int, default=42, help='Seed для random')

    def _find_model(self, model_name):
        for model in apps.get_models():
            if model.__name__.lower() == model_name.lower():
                return model
        return None

    def _choice_value(self, field, preferred=None):
        choices = getattr(field, 'choices', None) or []
        if not choices:
            return None

        flat = []
        for choice in choices:
            if isinstance(choice[1], (list, tuple)):
                for sub in choice[1]:
                    flat.append(sub[0])
            else:
                flat.append(choice[0])

        if preferred:
            normalized = {str(v).lower(): v for v in flat}
            for wanted in preferred:
                if str(wanted).lower() in normalized:
                    return normalized[str(wanted).lower()]

        return flat[0] if flat else None

    def _is_required(self, field):
        return (
            not getattr(field, 'null', False)
            and not getattr(field, 'blank', False)
            and not getattr(field, 'auto_created', False)
            and not getattr(field, 'primary_key', False)
            and not getattr(field, 'has_default', lambda: False)()
        )

    def _build_unique_tracking_value(self, Shipment, field, seed_index):
        max_length = getattr(field, 'max_length', None) or 32
        # Робимо номер тільки з цифр, бо в подібних моделях часто є додаткова валідація.
        # Беремо часову основу + індекс і, якщо потрібно, зсуваємо, доки не знайдемо вільне значення.
        base_num = int(timezone.now().strftime('%y%m%d%H%M%S%f')) + seed_index
        for offset in range(100000):
            raw = str(base_num + offset)
            candidate = raw[-max_length:] if len(raw) > max_length else raw.zfill(max_length)
            if not Shipment.objects.filter(**{field.name: candidate}).exists():
                return candidate
        raise CommandError(f'Не вдалося згенерувати унікальне значення для поля {field.name}')

    def _generic_value(self, field, index, context, Shipment=None):
        if getattr(field, 'choices', None):
            return self._choice_value(field)

        lower_name = field.name.lower()
        if Shipment is not None and isinstance(field, (models.CharField, models.TextField)):
            if lower_name in {'tracking_number', 'tracking_code', 'shipment_number', 'number'}:
                return self._build_unique_tracking_value(Shipment, field, index)

        if isinstance(field, (models.CharField, models.TextField)):
            value = f'Seed {field.name} {index}'
            if getattr(field, 'max_length', None):
                return value[:field.max_length]
            return value

        if isinstance(field, models.EmailField):
            value = f'seed{index}@example.com'
            if getattr(field, 'max_length', None):
                return value[:field.max_length]
            return value

        if isinstance(field, models.BooleanField):
            return False

        if isinstance(field, (models.IntegerField, models.BigIntegerField, models.PositiveIntegerField, models.PositiveBigIntegerField, models.SmallIntegerField, models.PositiveSmallIntegerField)):
            return 1

        if isinstance(field, models.DecimalField):
            return Decimal('100.00')

        if isinstance(field, models.FloatField):
            return 1.0

        if isinstance(field, models.DateTimeField):
            return timezone.now()

        if isinstance(field, models.DateField):
            return timezone.localdate()

        if isinstance(field, models.ForeignKey):
            rel_model = field.remote_field.model
            if rel_model is None:
                return None
            return rel_model.objects.order_by('pk').first()

        return None

    def _build_payload(self, Shipment, shipment_index, context):
        payload = {}
        fields = [
            f for f in Shipment._meta.get_fields()
            if isinstance(f, models.Field) and not f.auto_created and not getattr(f, 'many_to_many', False)
        ]

        origin = context['origin']
        destination = context['destination']
        sender = context['sender']
        recipient = context['recipient']
        origin_worker = context['origin_worker']

        special_values = {
            'sender': sender,
            'recipient': recipient,
            'created_by': origin_worker or sender,
            'accepted_by': origin_worker,
            'origin': origin,
            'origin_location': origin,
            'source_location': origin,
            'from_location': origin,
            'origin_post_office': origin,
            'sender_location': origin,
            'current_location': origin,
            'location': origin,
            'destination': destination,
            'destination_location': destination,
            'to_location': destination,
            'destination_post_office': destination,
            'recipient_location': destination,
            'pickup_location': origin,
            'delivery_location': destination,
            'region': getattr(origin.city, 'region', None),
            'city': getattr(origin, 'city', None),
            'sender_name': getattr(sender, 'full_name', None) or sender.get_full_name() or sender.username,
            'recipient_name': getattr(recipient, 'full_name', None) or recipient.get_full_name() or recipient.username,
            'sender_phone': getattr(sender, 'phone', None),
            'recipient_phone': getattr(recipient, 'phone', None),
            'sender_email': getattr(sender, 'email', None),
            'recipient_email': getattr(recipient, 'email', None),
            'weight': Decimal(str(round(random.uniform(0.2, 20.0), 2))),
            'declared_value': Decimal(str(random.randint(200, 5000))),
            'price': Decimal(str(random.randint(80, 350))),
            'cost': Decimal(str(random.randint(80, 350))),
            'delivery_cost': Decimal(str(random.randint(80, 350))),
            'amount': Decimal(str(random.randint(80, 350))),
            'total_price': Decimal(str(random.randint(80, 350))),
            'quantity': 1,
            'length': 10,
            'width': 10,
            'height': 10,
            'is_paid': False,
            'is_fragile': False,
            'fragile': False,
            'description': f'Тестова посилка #{shipment_index}',
            'note': 'Створено через seed',
            'notes': 'Створено через seed',
            'comment': 'Створено через seed',
            'address': f'Адреса відправлення: {origin.address}',
            'destination_address': f'Адреса отримання: {destination.address}',
        }

        for field in fields:
            if field.name in special_values and special_values[field.name] is not None:
                payload[field.name] = special_values[field.name]
                continue

            lower_name = field.name.lower()

            if lower_name in {'tracking_code', 'tracking_number', 'shipment_number', 'number'}:
                payload[field.name] = self._build_unique_tracking_value(Shipment, field, shipment_index)
                continue

            if lower_name in {'package_size', 'size'}:
                payload[field.name] = self._choice_value(
                    field,
                    preferred=['m', 'medium', 'size_m', 'small', 's', 'big_letter', 'letter']
                )
                continue

            if lower_name in {'payment_type', 'payment_method'}:
                payload[field.name] = self._choice_value(
                    field,
                    preferred=['sender_pays', 'sender', 'paid_by_sender', 'cash']
                )
                continue

            if lower_name in {'status', 'shipment_status'}:
                payload[field.name] = self._choice_value(
                    field,
                    preferred=['at_post_office', 'created', 'new', 'pending', 'registered', 'accepted']
                )
                continue

            if lower_name in {'shipment_type', 'type'} and getattr(field, 'choices', None):
                payload[field.name] = self._choice_value(field)
                continue

        for field in fields:
            if field.name in payload:
                continue
            if not self._is_required(field):
                continue
            generic = self._generic_value(field, shipment_index, context, Shipment=Shipment)
            if generic is not None:
                payload[field.name] = generic

        return payload

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options['seed'])

        Shipment = self._find_model('Shipment')
        if Shipment is None:
            raise CommandError('Не знайдено модель Shipment. Переконайся, що app з посилками доданий у INSTALLED_APPS.')

        from accounts.models import User, Role
        from locations.models import Location, LocationType

        if options['clear']:
            self.stdout.write('Очищення посилок...')
            Shipment.objects.all().delete()

        post_offices = list(Location.objects.filter(type=LocationType.POST_OFFICE).order_by('code'))
        if not post_offices:
            raise CommandError('Не знайдено жодного поштового відділення. Спочатку виконай seed_locations.')

        customers = list(User.objects.filter(role=Role.CUSTOMER).order_by('id'))
        if len(customers) < 2:
            raise CommandError('Потрібно мінімум 2 клієнти. Спочатку виконай seed_users.')

        total = options['count']
        created = 0

        self.stdout.write(f'Створення {total} посилок...')

        for i in range(1, total + 1):
            origin = post_offices[(i - 1) % len(post_offices)]
            destination_candidates = [po for po in post_offices if po.id != origin.id]
            if not destination_candidates:
                raise CommandError('Потрібно мінімум 2 різних поштових відділення для створення посилок.')
            destination = random.choice(destination_candidates)

            sender = customers[(i - 1) % len(customers)]
            recipient_candidates = [u for u in customers if u.id != sender.id]
            recipient = random.choice(recipient_candidates)

            origin_worker = User.objects.filter(
                role=Role.POSTAL_WORKER,
                location=origin,
            ).order_by('id').first()

            context = {
                'origin': origin,
                'destination': destination,
                'sender': sender,
                'recipient': recipient,
                'origin_worker': origin_worker,
            }

            payload = self._build_payload(Shipment, i, context)

            try:
                shipment = Shipment(**payload)
                shipment.save()
                created += 1
                tracking_display = (
                    getattr(shipment, 'tracking_number', None)
                    or getattr(shipment, 'tracking_code', None)
                    or getattr(shipment, 'shipment_number', None)
                    or shipment.pk
                )
                self.stdout.write(
                    f"  + #{created}: {tracking_display} | {origin.code} -> {destination.code}"
                )
            except Exception as exc:
                raise CommandError(
                    'Не вдалося створити посилку. '
                    f'Помилка: {exc}. '
                    f'Поля, які намагались заповнити: {sorted(payload.keys())}'
                )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Успішно створено {created} посилок'))
