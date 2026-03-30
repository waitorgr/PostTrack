from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RouteStatus(models.TextChoices):
    DRAFT = 'draft', 'Чернетка'
    CONFIRMED = 'confirmed', 'Підтверджено'
    IN_PROGRESS = 'in_progress', 'Виконується'
    COMPLETED = 'completed', 'Виконано'
    CANCELLED = 'cancelled', 'Скасовано'


class RouteStepType(models.TextChoices):
    ORIGIN = 'origin', 'Стартова точка'
    TRANSIT = 'transit', 'Проміжна точка'
    DESTINATION = 'destination', 'Кінцева точка'


class Route(models.Model):
    driver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes',
        verbose_name='Водій',
    )
    dispatch_group = models.OneToOneField(
        'dispatch.DispatchGroup',
        on_delete=models.PROTECT,
        related_name='route',
        verbose_name='Dispatch група',
    )
    origin = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='route_origins',
        verbose_name='Звідки',
    )
    destination = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='route_destinations',
        verbose_name='Куди',
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=RouteStatus.choices,
        default=RouteStatus.DRAFT,
        db_index=True,
    )
    is_auto = models.BooleanField('Автоматично згенерований', default=False)
    scheduled_departure = models.DateTimeField('Запланований виїзд')
    notes = models.TextField('Нотатки', blank=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_routes',
        verbose_name='Створив',
    )
    created_at = models.DateTimeField('Створено', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='route_status_created_idx'),
            models.Index(fields=['driver', 'status'], name='route_driver_status_idx'),
            models.Index(fields=['scheduled_departure'], name='route_scheduled_departure_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(origin=models.F('destination')),
                name='route_origin_not_destination',
            ),
        ]

    def __str__(self):
        group_label = getattr(self.dispatch_group, 'code', self.dispatch_group_id)
        driver_label = None

        if self.driver:
            driver_label = (
                getattr(self.driver, 'full_name', None)
                or getattr(self.driver, 'username', None)
                or getattr(self.driver, 'email', None)
                or str(self.driver)
            )

        return f'Маршрут {group_label} → {driver_label or "без водія"}'

    @property
    def is_editable(self):
        return self.status in {RouteStatus.DRAFT, RouteStatus.CONFIRMED}

    @property
    def step_count(self):
        if hasattr(self, '_step_count'):
            return self._step_count
        return self.steps.count()

    def clean(self):
        errors = {}

        if not self.dispatch_group_id:
            errors['dispatch_group'] = 'Потрібно вказати dispatch-групу.'
        else:
            dispatch_group = self.dispatch_group

            if not self.origin_id:
                self.origin = dispatch_group.origin
            if not self.destination_id:
                self.destination = dispatch_group.destination

            if self.origin_id != dispatch_group.origin_id:
                errors['origin'] = 'Origin маршруту має збігатися з origin dispatch-групи.'

            if self.destination_id != dispatch_group.destination_id:
                errors['destination'] = 'Destination маршруту має збігатися з destination dispatch-групи.'

            if self.driver_id and getattr(dispatch_group, 'driver_id', None) and self.driver_id != dispatch_group.driver_id:
                errors['driver'] = 'Водій маршруту має збігатися з водієм dispatch-групи.'

        if self.origin_id and self.destination_id and self.origin_id == self.destination_id:
            errors['destination'] = 'Локація призначення не може збігатися з локацією відправлення.'

        if self.driver_id:
            try:
                from accounts.models import Role

                driver_role = getattr(Role, 'DRIVER', 'driver')
                if getattr(self.driver, 'role', None) != driver_role:
                    errors['driver'] = 'Вказаний користувач не є водієм.'
            except Exception:
                pass

        if self._state.adding and self.status != RouteStatus.DRAFT:
            errors['status'] = 'Новий маршрут можна створювати лише у статусі "Чернетка".'

        if self.pk and self.status in {
            RouteStatus.CONFIRMED,
            RouteStatus.IN_PROGRESS,
            RouteStatus.COMPLETED,
        }:
            steps_qs = self.steps.all().order_by('order', 'id')
            steps_count = steps_qs.count()

            if steps_count < 2:
                errors['status'] = 'Маршрут має містити щонайменше 2 кроки: старт і фініш.'
            else:
                first_step = steps_qs.first()
                last_step = steps_qs.last()

                if first_step.step_type != RouteStepType.ORIGIN:
                    errors['status'] = 'Перший крок маршруту має бути стартовою точкою.'

                if last_step.step_type != RouteStepType.DESTINATION:
                    errors['status'] = 'Останній крок маршруту має бути кінцевою точкою.'

                if first_step.location_id != self.origin_id:
                    errors['origin'] = 'Перший крок маршруту має збігатися з origin маршруту.'

                if last_step.location_id != self.destination_id:
                    errors['destination'] = 'Останній крок маршруту має збігатися з destination маршруту.'

                origin_steps = steps_qs.filter(step_type=RouteStepType.ORIGIN).count()
                destination_steps = steps_qs.filter(step_type=RouteStepType.DESTINATION).count()

                if origin_steps != 1:
                    errors['status'] = 'Маршрут повинен містити рівно один стартовий крок.'

                if destination_steps != 1:
                    errors['status'] = 'Маршрут повинен містити рівно один кінцевий крок.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        touched_fields = set()
        update_fields = kwargs.get('update_fields')

        if self.dispatch_group_id:
            dispatch_group = self.dispatch_group

            if self.origin_id != dispatch_group.origin_id:
                self.origin = dispatch_group.origin
                touched_fields.add('origin')

            if self.destination_id != dispatch_group.destination_id:
                self.destination = dispatch_group.destination
                touched_fields.add('destination')

            if not self.driver_id and getattr(dispatch_group, 'driver_id', None):
                self.driver = dispatch_group.driver
                touched_fields.add('driver')

        if update_fields is not None and touched_fields:
            kwargs['update_fields'] = set(update_fields) | touched_fields

        self.full_clean()
        return super().save(*args, **kwargs)


class RouteStep(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='Маршрут',
    )
    order = models.PositiveSmallIntegerField('Порядок', db_index=True)
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='route_steps',
        verbose_name='Локація',
    )
    step_type = models.CharField(
        'Тип кроку',
        max_length=20,
        choices=RouteStepType.choices,
        default=RouteStepType.TRANSIT,
        db_index=True,
    )
    planned_arrival = models.DateTimeField('Планове прибуття', null=True, blank=True)
    planned_departure = models.DateTimeField('Плановий виїзд', null=True, blank=True)
    actual_arrival = models.DateTimeField('Фактичне прибуття', null=True, blank=True)
    actual_departure = models.DateTimeField('Фактичний виїзд', null=True, blank=True)
    notes = models.TextField('Нотатки', blank=True)
    created_at = models.DateTimeField('Створено', default=timezone.now)

    class Meta:
        verbose_name = 'Крок маршруту'
        verbose_name_plural = 'Кроки маршруту'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['route', 'order'], name='route_step_route_order_idx'),
            models.Index(fields=['route', 'step_type'], name='route_step_route_type_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['route', 'order'],
                name='route_step_unique_route_order',
            ),
            models.CheckConstraint(
                condition=models.Q(planned_arrival__isnull=True)
                | models.Q(planned_departure__isnull=True)
                | models.Q(planned_departure__gte=models.F('planned_arrival')),
                name='route_step_planned_departure_after_arrival',
            ),
            models.CheckConstraint(
                condition=models.Q(actual_arrival__isnull=True)
                | models.Q(actual_departure__isnull=True)
                | models.Q(actual_departure__gte=models.F('actual_arrival')),
                name='route_step_actual_departure_after_arrival',
            ),
        ]

    def __str__(self):
        route_label = getattr(self.route, 'dispatch_group_id', None)
        location_label = (
            getattr(self.location, 'name', None)
            or getattr(self.location, 'title', None)
            or getattr(self.location, 'code', None)
            or str(self.location)
        )
        return f'Крок {self.order} маршруту {route_label}: {location_label}'

    @property
    def is_completed(self):
        if self.step_type == RouteStepType.ORIGIN:
            return self.actual_departure is not None
        if self.step_type == RouteStepType.DESTINATION:
            return self.actual_arrival is not None
        return self.actual_arrival is not None and self.actual_departure is not None

    def clean(self):
        errors = {}

        if not self.route_id:
            errors['route'] = 'Потрібно вказати маршрут.'

        if not self.location_id:
            errors['location'] = 'Потрібно вказати локацію.'

        if self.order is not None and self.order < 1:
            errors['order'] = 'Порядок кроку має бути більше нуля.'

        if self.route_id:
            if self.route.status not in {RouteStatus.DRAFT, RouteStatus.CONFIRMED}:
                errors['route'] = 'Редагувати кроки можна лише у маршруті зі статусом "Чернетка" або "Підтверджено".'

            if self.step_type == RouteStepType.ORIGIN and self.route.origin_id and self.location_id != self.route.origin_id:
                errors['location'] = 'Стартовий крок має збігатися з origin маршруту.'

            if self.step_type == RouteStepType.DESTINATION and self.route.destination_id and self.location_id != self.route.destination_id:
                errors['location'] = 'Кінцевий крок має збігатися з destination маршруту.'

        if self.planned_arrival and self.planned_departure and self.planned_departure < self.planned_arrival:
            errors['planned_departure'] = 'Плановий виїзд не може бути раніше планового прибуття.'

        if self.actual_arrival and self.actual_departure and self.actual_departure < self.actual_arrival:
            errors['actual_departure'] = 'Фактичний виїзд не може бути раніше фактичного прибуття.'

        if self.step_type == RouteStepType.ORIGIN and self.actual_arrival:
            errors['actual_arrival'] = 'Для стартового кроку фактичне прибуття не використовується.'

        if self.step_type == RouteStepType.DESTINATION and self.actual_departure:
            errors['actual_departure'] = 'Для кінцевого кроку фактичний виїзд не використовується.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        touched_fields = set()
        update_fields = kwargs.get('update_fields')

        if self.route_id:
            if self.step_type == RouteStepType.ORIGIN and self.location_id != self.route.origin_id:
                self.location = self.route.origin
                touched_fields.add('location')

            if self.step_type == RouteStepType.DESTINATION and self.location_id != self.route.destination_id:
                self.location = self.route.destination
                touched_fields.add('location')

        if update_fields is not None and touched_fields:
            kwargs['update_fields'] = set(update_fields) | touched_fields

        self.full_clean()
        return super().save(*args, **kwargs)