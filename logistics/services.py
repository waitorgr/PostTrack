from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from .models import Route, RouteStep, RouteStatus, RouteStepType


class RouteService:
    @staticmethod
    def _raise_as_value_error(exc):
        if hasattr(exc, 'message_dict'):
            messages = []
            for value in exc.message_dict.values():
                if isinstance(value, (list, tuple)):
                    messages.extend([str(v) for v in value if v])
                elif value:
                    messages.append(str(value))
            raise ValueError(messages[0] if messages else 'Помилка валідації.')

        if hasattr(exc, 'messages') and exc.messages:
            raise ValueError(exc.messages[0])

        raise ValueError(str(exc))

    @staticmethod
    def _ensure_editable(route: Route):
        if not route.is_editable:
            raise ValueError('Маршрут можна редагувати лише у статусі "Чернетка" або "Підтверджено".')

    @staticmethod
    def _ensure_driver(route: Route):
        if not route.driver_id:
            raise ValueError('Для маршруту потрібно призначити водія.')

    @staticmethod
    def _get_step_blueprints(route: Route):
        return [
            {
                'step_type': step.step_type,
                'location_id': step.location_id,
                'planned_arrival': step.planned_arrival,
                'planned_departure': step.planned_departure,
                'actual_arrival': step.actual_arrival,
                'actual_departure': step.actual_departure,
                'notes': step.notes,
            }
            for step in route.steps.all().order_by('order', 'id')
        ]

    @staticmethod
    def _rebuild_steps(route: Route, blueprints):
        route.steps.all().delete()

        created_steps = []
        for index, blueprint in enumerate(blueprints, start=1):
            step = RouteStep(
                route=route,
                order=index,
                step_type=blueprint['step_type'],
                location_id=blueprint['location_id'],
                planned_arrival=blueprint.get('planned_arrival'),
                planned_departure=blueprint.get('planned_departure'),
                actual_arrival=blueprint.get('actual_arrival'),
                actual_departure=blueprint.get('actual_departure'),
                notes=blueprint.get('notes', ''),
            )
            step.save()
            created_steps.append(step)

        return created_steps

    @staticmethod
    def _normalize_custom_path(route: Route, location_ids):
        ids = []

        for value in location_ids or []:
            location_id = getattr(value, 'pk', value)
            if not location_id:
                continue
            ids.append(location_id)

        if not ids:
            return [route.origin_id, route.destination_id]

        if ids[0] != route.origin_id:
            ids.insert(0, route.origin_id)

        if ids[-1] != route.destination_id:
            ids.append(route.destination_id)

        for location_id in ids[1:-1]:
            if location_id == route.origin_id:
                raise ValueError('Origin не може бути проміжним кроком маршруту.')
            if location_id == route.destination_id:
                raise ValueError('Destination не може бути проміжним кроком маршруту.')

        return ids

    @staticmethod
    def _sync_dispatch_group_driver(route: Route):
        dispatch_group = route.dispatch_group

        if not route.driver_id:
            return

        if getattr(dispatch_group, 'driver_id', None) in (None, route.driver_id):
            if dispatch_group.driver_id != route.driver_id:
                dispatch_group.driver = route.driver
                dispatch_group.save(update_fields=['driver'])
            return

        raise ValueError('Водій маршруту не збігається з водієм dispatch-групи.')

    @staticmethod
    def _depart_dispatch_group(route: Route, started_by):
        try:
            from dispatch.services import DispatchService
        except Exception:
            return

        dispatch_group = route.dispatch_group
        dispatch_status = getattr(dispatch_group, 'status', None)

        if dispatch_status == 'forming':
            if not dispatch_group.items.exists():
                raise ValueError('Dispatch-група порожня і не готова до відправки.')
            DispatchService.mark_ready(dispatch_group, started_by)
            dispatch_group.refresh_from_db()
            dispatch_status = dispatch_group.status

        if dispatch_status == 'ready':
            DispatchService.depart(dispatch_group, started_by)
            return

        if dispatch_status == 'in_transit':
            return

        raise ValueError('Dispatch-група не готова до старту маршруту.')

    @staticmethod
    def _arrive_dispatch_group(route: Route, completed_by):
        try:
            from dispatch.services import DispatchService
        except Exception:
            return

        dispatch_group = route.dispatch_group
        dispatch_status = getattr(dispatch_group, 'status', None)

        if dispatch_status == 'in_transit':
            DispatchService.arrive(dispatch_group, completed_by)
            return

        if dispatch_status in {'arrived', 'completed'}:
            return

        raise ValueError('Dispatch-група не перебуває в статусі доставки.')

    @staticmethod
    @transaction.atomic
    def generate_default_steps(route: Route, transit_location_ids=None, replace_existing=False):
        RouteService._ensure_editable(route)

        if route.steps.exists() and not replace_existing:
            raise ValueError('У маршруті вже є кроки. Для перегенерації потрібно replace_existing=True.')

        ids = [route.origin_id]
        for value in transit_location_ids or []:
            location_id = getattr(value, 'pk', value)
            if not location_id:
                continue
            if location_id in {route.origin_id, route.destination_id}:
                continue
            ids.append(location_id)
        ids.append(route.destination_id)

        blueprints = []
        for index, location_id in enumerate(ids):
            if index == 0:
                step_type = RouteStepType.ORIGIN
                planned_departure = route.scheduled_departure
                planned_arrival = None
            elif index == len(ids) - 1:
                step_type = RouteStepType.DESTINATION
                planned_departure = None
                planned_arrival = None
            else:
                step_type = RouteStepType.TRANSIT
                planned_departure = None
                planned_arrival = None

            blueprints.append({
                'step_type': step_type,
                'location_id': location_id,
                'planned_arrival': planned_arrival,
                'planned_departure': planned_departure,
                'actual_arrival': None,
                'actual_departure': None,
                'notes': '',
            })

        created_steps = RouteService._rebuild_steps(route, blueprints)

        route.is_auto = True
        route.save(update_fields=['is_auto'])

        return created_steps

    @staticmethod
    @transaction.atomic
    def replace_steps(route: Route, location_ids, updated_by=None):
        RouteService._ensure_editable(route)

        normalized_ids = RouteService._normalize_custom_path(route, location_ids)

        blueprints = []
        for index, location_id in enumerate(normalized_ids):
            if index == 0:
                step_type = RouteStepType.ORIGIN
                planned_departure = route.scheduled_departure
                planned_arrival = None
            elif index == len(normalized_ids) - 1:
                step_type = RouteStepType.DESTINATION
                planned_departure = None
                planned_arrival = None
            else:
                step_type = RouteStepType.TRANSIT
                planned_departure = None
                planned_arrival = None

            blueprints.append({
                'step_type': step_type,
                'location_id': location_id,
                'planned_arrival': planned_arrival,
                'planned_departure': planned_departure,
                'actual_arrival': None,
                'actual_departure': None,
                'notes': '',
            })

        created_steps = RouteService._rebuild_steps(route, blueprints)

        route.is_auto = False
        route.save(update_fields=['is_auto'])

        return created_steps

    @staticmethod
    @transaction.atomic
    def add_step(
        route: Route,
        location,
        order=None,
        planned_arrival=None,
        planned_departure=None,
        notes='',
    ):
        RouteService._ensure_editable(route)

        location_id = getattr(location, 'pk', location)
        if not location_id:
            raise ValueError('Потрібно вказати локацію для кроку.')

        if location_id in {route.origin_id, route.destination_id}:
            raise ValueError('Origin і destination не можна додавати як транзитний крок.')

        blueprints = RouteService._get_step_blueprints(route)
        if len(blueprints) < 2:
            raise ValueError('Спочатку маршрут повинен містити стартовий і кінцевий крок.')

        destination_index = len(blueprints) - 1

        if order is None:
            insert_index = destination_index
        else:
            insert_index = order - 1

        if insert_index < 1 or insert_index > destination_index:
            raise ValueError('Транзитний крок можна вставити лише між стартом і фінішем.')

        blueprints.insert(insert_index, {
            'step_type': RouteStepType.TRANSIT,
            'location_id': location_id,
            'planned_arrival': planned_arrival,
            'planned_departure': planned_departure,
            'actual_arrival': None,
            'actual_departure': None,
            'notes': notes or '',
        })

        return RouteService._rebuild_steps(route, blueprints)

    @staticmethod
    @transaction.atomic
    def update_step(
        step: RouteStep,
        location=None,
        order=None,
        planned_arrival=None,
        planned_departure=None,
        notes=None,
    ):
        route = step.route
        RouteService._ensure_editable(route)

        blueprints = RouteService._get_step_blueprints(route)

        target_index = None
        ordered_steps = list(route.steps.all().order_by('order', 'id'))
        for index, existing_step in enumerate(ordered_steps):
            if existing_step.id == step.id:
                target_index = index
                break

        if target_index is None:
            raise ValueError('Крок маршруту не знайдено.')

        blueprint = blueprints[target_index]

        if step.step_type in {RouteStepType.ORIGIN, RouteStepType.DESTINATION}:
            if location is not None or order is not None:
                raise ValueError('Стартовий і кінцевий кроки не можна переносити або змінювати їхню локацію.')

            if planned_arrival is not None:
                blueprint['planned_arrival'] = planned_arrival
            if planned_departure is not None:
                blueprint['planned_departure'] = planned_departure
            if notes is not None:
                blueprint['notes'] = notes

            blueprints[target_index] = blueprint
            return RouteService._rebuild_steps(route, blueprints)

        if location is not None:
            location_id = getattr(location, 'pk', location)
            if not location_id:
                raise ValueError('Потрібно вказати коректну локацію.')
            if location_id in {route.origin_id, route.destination_id}:
                raise ValueError('Транзитний крок не може збігатися з origin або destination.')
            blueprint['location_id'] = location_id

        if planned_arrival is not None:
            blueprint['planned_arrival'] = planned_arrival
        if planned_departure is not None:
            blueprint['planned_departure'] = planned_departure
        if notes is not None:
            blueprint['notes'] = notes

        blueprints.pop(target_index)

        destination_index = len(blueprints) - 1
        if order is None:
            insert_index = target_index
        else:
            insert_index = order - 1

        if insert_index < 1 or insert_index > destination_index:
            raise ValueError('Транзитний крок можна розташувати лише між стартом і фінішем.')

        blueprints.insert(insert_index, blueprint)

        return RouteService._rebuild_steps(route, blueprints)

    @staticmethod
    @transaction.atomic
    def remove_step(step: RouteStep):
        route = step.route
        RouteService._ensure_editable(route)

        if step.step_type in {RouteStepType.ORIGIN, RouteStepType.DESTINATION}:
            raise ValueError('Стартовий і кінцевий кроки не можна видаляти.')

        blueprints = RouteService._get_step_blueprints(route)

        ordered_steps = list(route.steps.all().order_by('order', 'id'))
        target_index = None
        for index, existing_step in enumerate(ordered_steps):
            if existing_step.id == step.id:
                target_index = index
                break

        if target_index is None:
            raise ValueError('Крок маршруту не знайдено.')

        blueprints.pop(target_index)
        return RouteService._rebuild_steps(route, blueprints)

    @staticmethod
    @transaction.atomic
    def confirm(route: Route, confirmed_by=None):
        if route.status != RouteStatus.DRAFT:
            raise ValueError('Підтвердити можна лише маршрут у статусі "Чернетка".')

        if not route.steps.exists():
            if route.is_auto:
                RouteService.generate_default_steps(route, replace_existing=True)
            else:
                raise ValueError('Неможливо підтвердити маршрут без кроків.')

        route.status = RouteStatus.CONFIRMED

        try:
            route.save(update_fields=['status'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return route

    @staticmethod
    @transaction.atomic
    def start(route: Route, started_by=None, sync_dispatch=True):
        if route.status != RouteStatus.CONFIRMED:
            raise ValueError('Запустити можна лише підтверджений маршрут.')

        RouteService._ensure_driver(route)

        first_step = route.steps.order_by('order', 'id').first()
        if not first_step:
            raise ValueError('Маршрут не містить жодного кроку.')

        RouteService._sync_dispatch_group_driver(route)

        if sync_dispatch:
            RouteService._depart_dispatch_group(route, started_by)

        if first_step.step_type != RouteStepType.ORIGIN:
            raise ValueError('Перший крок маршруту має бути стартовою точкою.')

        if first_step.actual_departure is None:
            first_step.actual_departure = timezone.now()
            first_step.save(update_fields=['actual_departure'])

        route.status = RouteStatus.IN_PROGRESS

        try:
            route.save(update_fields=['status'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return route

    @staticmethod
    @transaction.atomic
    def mark_step_arrival(step: RouteStep, arrived_at=None):
        route = step.route

        if route.status != RouteStatus.IN_PROGRESS:
            raise ValueError('Фактичне прибуття можна фіксувати лише для маршруту в роботі.')

        if step.step_type == RouteStepType.ORIGIN:
            raise ValueError('Для стартового кроку прибуття не фіксується.')

        step.actual_arrival = arrived_at or timezone.now()

        try:
            step.save(update_fields=['actual_arrival'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return step

    @staticmethod
    @transaction.atomic
    def mark_step_departure(step: RouteStep, departed_at=None):
        route = step.route

        if route.status != RouteStatus.IN_PROGRESS:
            raise ValueError('Фактичний виїзд можна фіксувати лише для маршруту в роботі.')

        if step.step_type == RouteStepType.DESTINATION:
            raise ValueError('Для кінцевого кроку виїзд не фіксується.')

        if step.step_type == RouteStepType.TRANSIT and not step.actual_arrival:
            raise ValueError('Для транзитного кроку спочатку потрібно зафіксувати прибуття.')

        step.actual_departure = departed_at or timezone.now()

        try:
            step.save(update_fields=['actual_departure'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return step

    @staticmethod
    @transaction.atomic
    def complete(route: Route, completed_by=None, sync_dispatch=True):
        if route.status != RouteStatus.IN_PROGRESS:
            raise ValueError('Завершити можна лише маршрут, який виконується.')

        last_step = route.steps.order_by('order', 'id').last()
        if not last_step:
            raise ValueError('Маршрут не містить жодного кроку.')

        if last_step.step_type != RouteStepType.DESTINATION:
            raise ValueError('Останній крок маршруту має бути кінцевою точкою.')

        if last_step.actual_arrival is None:
            arrival_time = timezone.now()
            type(last_step).objects.filter(pk=last_step.pk).update(actual_arrival=arrival_time)
            last_step.actual_arrival = arrival_time

        if sync_dispatch:
            RouteService._arrive_dispatch_group(route, completed_by)

        route.status = RouteStatus.COMPLETED

        try:
            route.save(update_fields=['status'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return route

    @staticmethod
    @transaction.atomic
    def cancel(route: Route, cancelled_by=None):
        if route.status == RouteStatus.COMPLETED:
            raise ValueError('Завершений маршрут не можна скасувати.')

        route.status = RouteStatus.CANCELLED

        try:
            route.save(update_fields=['status'])
        except DjangoValidationError as exc:
            RouteService._raise_as_value_error(exc)

        return route