from tokenize import group

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from .models import DispatchGroup, DispatchGroupItem, DispatchGroupStatus
from shipments.models import ShipmentStatus
from tracking.utils import create_tracking_event


class DispatchService:
    @staticmethod
    def _location_label(location):
        if location is None:
            return 'невідому локацію'

        for attr in ('name', 'title', 'code'):
            value = getattr(location, attr, None)
            if value not in (None, ''):
                return value

        return str(location)

    @staticmethod
    def _shipment_save_update_fields(shipment):
        fields = {'status'}

        concrete_fields = {
            field.name
            for field in shipment._meta.concrete_fields
        }

        if 'updated_at' in concrete_fields:
            fields.add('updated_at')

        return list(fields)

    @staticmethod
    def _raise_as_value_error(exc):
        if hasattr(exc, 'message_dict'):
            first_error = []
            for messages in exc.message_dict.values():
                if isinstance(messages, (list, tuple)) and messages:
                    first_error.append(str(messages[0]))
                elif messages:
                    first_error.append(str(messages))
            raise ValueError(first_error[0] if first_error else 'Помилка валідації.')
        if hasattr(exc, 'messages') and exc.messages:
            raise ValueError(exc.messages[0])
        raise ValueError(str(exc))

    @staticmethod
    def get_or_create_open_group(origin, destination, created_by=None):
        group = (
            DispatchGroup.objects.filter(
                origin=origin,
                destination=destination,
                status__in=(DispatchGroupStatus.FORMING, DispatchGroupStatus.READY),
            )
            .order_by('status', '-created_at')
            .first()
        )

        created = False
        if group is None:
            group = DispatchGroup.objects.create(
                origin=origin,
                destination=destination,
                current_location=origin,
                created_by=created_by,
            )
            created = True

        return group, created

    @staticmethod
    @transaction.atomic
    def add_shipment(group: DispatchGroup, shipment, added_by):
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            raise ValueError('Додавати посилки можна лише до групи, яка ще не відправлена.')

        item = DispatchGroupItem(
            group=group,
            shipment=shipment,
            added_by=added_by,
        )

        try:
            current_location = DispatchService.get_shipment_current_location(shipment)
            next_hop = DispatchService.get_shipment_next_hop(shipment)

            if current_location is None:
                raise ValueError('У посилки не визначена поточна локація.')

            if current_location.id != group.origin_id:
                raise ValueError('Посилка не знаходиться в origin цієї dispatch-групи.')

            if next_hop is None:
                raise ValueError('Для посилки не визначено наступний крок маршруту.')

            if next_hop.id != group.destination_id:
                raise ValueError('Наступний крок посилки не збігається з destination цієї dispatch-групи.')
            item.save()
        except DjangoValidationError as exc:
            DispatchService._raise_as_value_error(exc)

        return item

    @staticmethod
    @transaction.atomic
    def remove_shipment(group: DispatchGroup, shipment, removed_by=None):
        if group.status not in (DispatchGroupStatus.FORMING, DispatchGroupStatus.READY):
            raise ValueError('Видалення можливе лише з групи, яка ще не відправлена.')

        item = DispatchGroupItem.objects.filter(
            group=group,
            shipment=shipment,
        ).first()

        if not item:
            raise ValueError('Посилку не знайдено в цій групі.')

        item.delete()

    @staticmethod
    @transaction.atomic
    def mark_ready(group: DispatchGroup, marked_by=None):
        if group.status != DispatchGroupStatus.FORMING:
            raise ValueError("У статус 'Готово' можна перевести лише групу, що формується.")

        if not group.items.exists():
            raise ValueError('Неможливо позначити готовою порожню групу.')

        group.status = DispatchGroupStatus.READY

        try:
            group.save(update_fields=['status'])
        except DjangoValidationError as exc:
            DispatchService._raise_as_value_error(exc)

        return group

    @staticmethod
    @transaction.atomic
    def depart(group: DispatchGroup, departed_by):
        if group.status != DispatchGroupStatus.READY:
            raise ValueError('Група ще не готова до відправки.')

        if not group.items.exists():
            raise ValueError('Неможливо відправити порожню групу.')

        if not group.driver_id:
            raise ValueError('Перед відправкою потрібно призначити водія.')

        group.status = DispatchGroupStatus.IN_TRANSIT
        group.departed_at = timezone.now()
        group.current_location = None

        try:
            group.save(update_fields=['status', 'departed_at', 'current_location', 'driver'])
        except DjangoValidationError as exc:
            DispatchService._raise_as_value_error(exc)

        destination_label = DispatchService._location_label(group.destination)

        for item in group.items.select_related('shipment'):
            shipment = item.shipment
            shipment.status = ShipmentStatus.PICKED_UP_BY_DRIVER
            shipment.save(update_fields=DispatchService._shipment_save_update_fields(shipment))

            create_tracking_event(
                shipment=shipment,
                event_type='picked_up_by_driver',
                location=group.origin,
                created_by=departed_by,
                note=f'Dispatch група {group.code} вирушила до {destination_label}.',
                is_public=True,
            )

        return group

    @staticmethod
    @transaction.atomic
    def arrive(group: DispatchGroup, arrived_by):
        if group.status != DispatchGroupStatus.IN_TRANSIT:
            raise ValueError('Група ще не відправлена або вже прибула.')

        from shipments.services import ShipmentService

        group.status = DispatchGroupStatus.ARRIVED
        group.arrived_at = timezone.now()
        group.current_location = group.destination

        try:
            group.save(update_fields=['status', 'arrived_at', 'current_location'])
        except DjangoValidationError as exc:
            DispatchService._raise_as_value_error(exc)

        for item in group.items.select_related('shipment'):
            shipment = item.shipment

            # 1. Просуваємо маршрут посилки:
            #    active step -> done
            #    next pending step -> active
            #    shipment.current_location -> destination
            ShipmentService.advance_route(
                shipment=shipment,
                arrived_location=group.destination,
                advanced_by=arrived_by,
            )

            # 2. Оновлюємо бізнес-статус посилки
            shipment.status = ShipmentStatus.ARRIVED_AT_FACILITY
            shipment.save(update_fields=DispatchService._shipment_save_update_fields(shipment))

        return group

    @staticmethod
    @transaction.atomic
    def complete(group: DispatchGroup, completed_by=None):
        if group.status != DispatchGroupStatus.ARRIVED:
            raise ValueError('Завершити можна лише групу, яка вже прибула.')

        group.status = DispatchGroupStatus.COMPLETED

        try:
            group.save(update_fields=['status'])
        except DjangoValidationError as exc:
            DispatchService._raise_as_value_error(exc)

        return group

    @staticmethod
    def get_shipment_next_hop(shipment):
        if hasattr(shipment, 'get_next_route_step'):
            step = shipment.get_next_route_step()
            return getattr(step, 'location', None) if step else None
    
        next_step = (
            shipment.route_steps
            .filter(status='pending')
            .order_by('order')
            .select_related('location')
            .first()
        )
        return next_step.location if next_step else None
    
    @staticmethod
    def get_shipment_current_location(shipment):
        return getattr(shipment, 'current_location', None)
    
    @staticmethod
    def get_or_create_open_group_for_shipment(shipment, created_by=None):
        origin = DispatchService.get_shipment_current_location(shipment)
        destination = DispatchService.get_shipment_next_hop(shipment)
    
        if origin is None:
            raise ValueError('У посилки не визначена поточна локація.')
        if destination is None:
            raise ValueError('У посилки не визначений наступний крок маршруту.')
    
        return DispatchService.get_or_create_open_group(
            origin=origin,
            destination=destination,
            created_by=created_by,
        )