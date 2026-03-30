from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.utils import timezone
from django.utils.crypto import get_random_string


GROUP_CODE_LENGTH = 6
GROUP_CODE_PREFIX = 'DG-'


def generate_group_code():
    """Генерує код dispatch-групи виду DG-123456."""
    return f"{GROUP_CODE_PREFIX}{get_random_string(GROUP_CODE_LENGTH, allowed_chars='0123456789')}"


class DispatchGroupStatus(models.TextChoices):
    FORMING = 'forming', 'Формується'
    READY = 'ready', 'Готово до відправки'
    IN_TRANSIT = 'in_transit', 'В дорозі'
    ARRIVED = 'arrived', 'Прибуло'
    COMPLETED = 'completed', 'Завершено'


class DispatchGroup(models.Model):
    code = models.CharField(
        'Код групи',
        max_length=20,
        unique=True,
        default=generate_group_code,
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=DispatchGroupStatus.choices,
        default=DispatchGroupStatus.FORMING,
        db_index=True,
    )
    origin = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='outgoing_groups',
        verbose_name='Звідки',
    )
    destination = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='incoming_groups',
        verbose_name='Куди',
    )
    driver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_groups',
        verbose_name='Водій',
    )
    current_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_groups',
        verbose_name='Поточна локація',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_groups',
        verbose_name='Створив',
    )
    departed_at = models.DateTimeField('Час відправки', null=True, blank=True)
    arrived_at = models.DateTimeField('Час прибуття', null=True, blank=True)
    created_at = models.DateTimeField('Створено', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Dispatch група'
        verbose_name_plural = 'Dispatch групи'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='dispatch_status_created_idx'),
            models.Index(fields=['origin', 'status'], name='dispatch_origin_status_idx'),
            models.Index(fields=['destination', 'status'], name='dispatch_dest_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(origin=models.F('destination')),
                name='dispatch_group_origin_not_destination',
            ),
            models.CheckConstraint(
                condition=models.Q(arrived_at__isnull=True) | models.Q(departed_at__isnull=False),
                name='dispatch_group_arrival_requires_departure',
            ),
            models.CheckConstraint(
                condition=models.Q(arrived_at__isnull=True) | models.Q(arrived_at__gte=models.F('departed_at')),
                name='dispatch_group_arrival_not_before_departure',
            ),
        ]

    def __str__(self):
        return f'{self.code} ({self.get_status_display()})'

    @property
    def is_editable(self):
        return self.status in {DispatchGroupStatus.FORMING, DispatchGroupStatus.READY}

    @property
    def is_active(self):
        return self.status != DispatchGroupStatus.COMPLETED

    def get_destination_location(self):
        """
        Автоматично визначає наступну локацію за ієрархією.
    
        POST_OFFICE -> distribution center
        DISTRIBUTION_CENTER -> sorting center
        Для інших типів повертає None.
        """
        if not self.origin:
            return None
    
        origin_type = getattr(self.origin, 'type', None)
    
        distribution_center_value = 'distribution_center'
        post_office_value = 'post_office'
    
        try:
            from locations.models import LocationType
            distribution_center_value = getattr(LocationType, 'DISTRIBUTION_CENTER', distribution_center_value)
            post_office_value = getattr(LocationType, 'POST_OFFICE', post_office_value)
        except Exception:
            pass
        
        if origin_type == post_office_value:
            if hasattr(self.origin, 'get_distribution_center'):
                dc = self.origin.get_distribution_center()
                if dc is not None:
                    return dc
    
            for attr in ('parent_dc', 'distribution_center', 'dc'):
                value = getattr(self.origin, attr, None)
                if value is not None:
                    return value
    
        if origin_type == distribution_center_value:
            if hasattr(self.origin, 'get_sorting_center'):
                sc = self.origin.get_sorting_center()
                if sc is not None:
                    return sc
    
            for attr in ('parent_sc', 'sorting_center', 'sc'):
                value = getattr(self.origin, attr, None)
                if value is not None:
                    return value
    
        return None

    def clean(self):
        errors = {}

        expected_destination = self.get_destination_location() if self.origin_id else None

        if not self.destination_id and expected_destination is not None:
            self.destination = expected_destination

        if not self.origin_id:
            errors['origin'] = 'Потрібно вказати локацію відправлення.'

        if not self.destination_id:
            errors['destination'] = 'Потрібно вказати локацію призначення.'

        if self.origin_id and self.destination_id and self.origin_id == self.destination_id:
            errors['destination'] = 'Локація призначення не може збігатися з локацією відправлення.'

        if expected_destination is not None and self.destination_id and self.destination_id != expected_destination.id:
            errors['destination'] = (
                f'Для локації "{self.origin}" наступною ланкою має бути "{expected_destination}".'
            )

        if self.driver_id:
            try:
                from accounts.models import Role

                driver_role = getattr(Role, 'DRIVER', 'driver')
                if getattr(self.driver, 'role', None) != driver_role:
                    errors['driver'] = 'Вказаний користувач не є водієм.'
            except Exception:
                pass

        if self.arrived_at and not self.departed_at:
            errors['arrived_at'] = 'Не можна вказати час прибуття без часу відправки.'

        if self.departed_at and self.arrived_at and self.arrived_at < self.departed_at:
            errors['arrived_at'] = 'Час прибуття не може бути раніше часу відправки.'

        if self.status == DispatchGroupStatus.FORMING:
            if self.departed_at:
                errors['departed_at'] = 'У статусі "Формується" не може бути часу відправки.'
            if self.arrived_at:
                errors['arrived_at'] = 'У статусі "Формується" не може бути часу прибуття.'
            if self.current_location_id and self.origin_id and self.current_location_id != self.origin_id:
                errors['current_location'] = 'Поки група формується, її поточна локація має збігатися з origin.'

        elif self.status == DispatchGroupStatus.READY:
            if self.departed_at:
                errors['departed_at'] = 'У статусі "Готово до відправки" не може бути часу відправки.'
            if self.arrived_at:
                errors['arrived_at'] = 'У статусі "Готово до відправки" не може бути часу прибуття.'
            if self.current_location_id and self.origin_id and self.current_location_id != self.origin_id:
                errors['current_location'] = 'Поки група не відправлена, вона має перебувати в origin.'

        elif self.status == DispatchGroupStatus.IN_TRANSIT:
            if not self.departed_at:
                errors['departed_at'] = 'Для статусу "В дорозі" потрібно вказати час відправки.'
            if self.arrived_at:
                errors['arrived_at'] = 'Група в дорозі ще не може мати часу прибуття.'
            if self.current_location_id is not None:
                errors['current_location'] = 'Під час руху current_location має бути порожнім.'
            if not self.driver_id:
                errors['driver'] = 'Для відправленої групи потрібно призначити водія.'

        elif self.status == DispatchGroupStatus.ARRIVED:
            if not self.departed_at:
                errors['departed_at'] = 'Для статусу "Прибуло" потрібен час відправки.'
            if not self.arrived_at:
                errors['arrived_at'] = 'Для статусу "Прибуло" потрібен час прибуття.'
            if self.destination_id and self.current_location_id != self.destination_id:
                errors['current_location'] = 'Після прибуття current_location має збігатися з destination.'
            if not self.driver_id:
                errors['driver'] = 'Для доставленої групи має бути вказаний водій.'

        elif self.status == DispatchGroupStatus.COMPLETED:
            if not self.departed_at:
                errors['departed_at'] = 'Для завершеної групи потрібен час відправки.'
            if not self.arrived_at:
                errors['arrived_at'] = 'Для завершеної групи потрібен час прибуття.'
            if self.destination_id and self.current_location_id != self.destination_id:
                errors['current_location'] = 'Завершена група має знаходитися в destination.'

        if self.status != DispatchGroupStatus.FORMING:
            if self._state.adding:
                errors['status'] = 'Нову групу можна створювати лише у статусі "Формується".'
            elif self.pk and not self.items.exists():
                errors['status'] = 'Не можна перевести порожню групу в цей статус.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_group_code()

        if not self.destination_id:
            inferred_destination = self.get_destination_location()
            if inferred_destination is not None:
                self.destination = inferred_destination

        if not self.current_location_id and self.status in {DispatchGroupStatus.FORMING, DispatchGroupStatus.READY}:
            self.current_location = self.origin

        attempts = 5 if self._state.adding else 1

        for attempt in range(attempts):
            self.full_clean()
            try:
                return super().save(*args, **kwargs)
            except IntegrityError as exc:
                if self._state.adding and 'code' in str(exc).lower() and attempt < attempts - 1:
                    self.code = generate_group_code()
                    continue
                raise


class DispatchGroupItem(models.Model):
    BLOCKING_GROUP_STATUSES = (
        DispatchGroupStatus.FORMING,
        DispatchGroupStatus.READY,
        DispatchGroupStatus.IN_TRANSIT,
        DispatchGroupStatus.ARRIVED,
    )

    group = models.ForeignKey(
        DispatchGroup,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Група',
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        on_delete=models.PROTECT,
        related_name='dispatch_items',
        verbose_name='Посилка',
    )
    added_at = models.DateTimeField('Додано', auto_now_add=True)
    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_items',
        verbose_name='Додав',
    )

    class Meta:
        verbose_name = 'Елемент Dispatch групи'
        verbose_name_plural = 'Елементи Dispatch груп'
        ordering = ['-added_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'shipment'],
                name='dispatch_group_item_unique_group_shipment',
            ),
        ]

    def __str__(self):
        shipment_label = getattr(self.shipment, 'tracking_number', self.shipment_id)
        group_label = getattr(self.group, 'code', self.group_id)
        return f'{group_label} → {shipment_label}'

    def clean(self):
        errors = {}

        if not self.group_id:
            errors['group'] = 'Потрібно вказати dispatch-групу.'

        if not self.shipment_id:
            errors['shipment'] = 'Потрібно вказати посилку.'

        if self.group_id:
            if self.group.status not in {DispatchGroupStatus.FORMING, DispatchGroupStatus.READY}:
                errors['group'] = 'Додавати посилки можна лише до групи у статусі "Формується" або "Готово до відправки".'

        if self.group_id and self.shipment_id:
            existing_item = (
                DispatchGroupItem.objects.filter(
                    shipment_id=self.shipment_id,
                    group__status__in=self.BLOCKING_GROUP_STATUSES,
                )
                .exclude(pk=self.pk)
                .select_related('group')
                .first()
            )
            if existing_item:
                errors['shipment'] = (
                    f'Посилка вже знаходиться в іншій активній dispatch-групі: {existing_item.group.code}.'
                )

        shipment_status = getattr(self.shipment, 'status', None)
        if shipment_status in {'cancelled', 'canceled'}:
            errors['shipment'] = 'Скасовану посилку не можна додавати до dispatch-групи.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)