from django.db import models
from django.core.exceptions import ValidationError


class LocationType(models.TextChoices):
    POST_OFFICE = 'post_office', 'Поштове відділення'
    SORTING_CENTER = 'sorting_center', 'Сортувальний центр'
    DISTRIBUTION_CENTER = 'distribution_center', 'Розподільчий центр'


class Region(models.Model):
    name = models.CharField('Назва регіону', max_length=100)
    code = models.CharField('Код регіону', max_length=10, unique=True)

    class Meta:
        verbose_name = 'Регіон'
        verbose_name_plural = 'Регіони'
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField('Назва міста', max_length=100)
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name='cities',
        verbose_name='Регіон'
    )

    class Meta:
        verbose_name = 'Місто'
        verbose_name_plural = 'Міста'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.region.name})'


class Location(models.Model):
    name = models.CharField('Назва', max_length=200)
    type = models.CharField('Тип', max_length=30, choices=LocationType.choices)
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name='locations',
        verbose_name='Місто'
    )
    address = models.CharField('Адреса', max_length=300)
    code = models.CharField('Код', max_length=20, unique=True)
    is_active = models.BooleanField('Активне', default=True)

    # Ієрархія: СЦ -> РЦ -> Відділення
    parent_sc = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='distribution_centers',
        verbose_name='Батьківський сортувальний центр',
        limit_choices_to={'type': LocationType.SORTING_CENTER}
    )
    parent_dc = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='post_offices',
        verbose_name='Батьківський розподільчий центр',
        limit_choices_to={'type': LocationType.DISTRIBUTION_CENTER}
    )

    class Meta:
        verbose_name = 'Локація'
        verbose_name_plural = 'Локації'
        ordering = ['code', 'name']

    def clean(self):
        """
        Валідація кодів:
        - SC: SS (2 цифри)
        - DC: SSRRR (5 цифр)
        - PO: SSRRRPPPPP (10 цифр)
        """
        if not self.code.isdigit():
            raise ValidationError('Код має містити тільки цифри')

        if self.type == LocationType.SORTING_CENTER:
            if len(self.code) != 2:
                raise ValidationError('Код сортувального центру має бути 2 цифри (SS)')
            if self.parent_sc or self.parent_dc:
                raise ValidationError('Сортувальний центр не може мати батьківську локацію')

        elif self.type == LocationType.DISTRIBUTION_CENTER:
            if len(self.code) != 5:
                raise ValidationError('Код розподільчого центру має бути 5 цифр (SSRRR)')
            if not self.parent_sc:
                raise ValidationError('Розподільчий центр повинен мати батьківський сортувальний центр')
            if self.parent_dc:
                raise ValidationError('Розподільчий центр не може мати батьківський РЦ')
            if not self.code.startswith(self.parent_sc.code):
                raise ValidationError(
                    f'Код має починатися з {self.parent_sc.code} (код батьківського СЦ)'
                )

        elif self.type == LocationType.POST_OFFICE:
            if len(self.code) != 10:
                raise ValidationError('Код відділення пошти має бути 10 цифр (SSRRRPPPPP)')
            if not self.parent_dc:
                raise ValidationError('Відділення пошти повинно мати батьківський розподільчий центр')
            if self.parent_sc:
                raise ValidationError('Відділення пошти має вказувати тільки РЦ, а не СЦ')
            if not self.code.startswith(self.parent_dc.code):
                raise ValidationError(
                    f'Код має починатися з {self.parent_dc.code} (код батьківського РЦ)'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def region(self):
        return self.city.region

    @property
    def level(self):
        if self.type == LocationType.SORTING_CENTER:
            return 1
        if self.type == LocationType.DISTRIBUTION_CENTER:
            return 2
        return 3

    def get_sorting_center(self):
        if self.type == LocationType.SORTING_CENTER:
            return self
        if self.type == LocationType.DISTRIBUTION_CENTER:
            return self.parent_sc
        if self.type == LocationType.POST_OFFICE:
            return self.parent_dc.parent_sc if self.parent_dc else None
        return None

    def get_distribution_center(self):
        if self.type == LocationType.DISTRIBUTION_CENTER:
            return self
        if self.type == LocationType.POST_OFFICE:
            return self.parent_dc
        return None

    def get_post_offices(self):
        if self.type == LocationType.DISTRIBUTION_CENTER:
            return self.post_offices.all()
        return Location.objects.none()

    def __str__(self):
        return f"{self.code} — {self.get_type_display()} — {self.name} ({self.city})"
    
    def get_parent_location(self):
        """
        Повертає безпосередню батьківську локацію в ієрархії:
        POST_OFFICE -> parent_dc
        DISTRIBUTION_CENTER -> parent_sc
        SORTING_CENTER -> None
        """
        if self.parent_dc_id:
            return self.parent_dc

        if self.parent_sc_id:
            return self.parent_sc

        return None


    def get_ancestors(self):
        """
        Повертає список усіх батьківських локацій вгору по ієрархії.
        Наприклад:
        post_office -> [distribution_center, sorting_center]
        distribution_center -> [sorting_center]
        sorting_center -> []
        """
        ancestors = []
        current = self.get_parent_location()
    
        while current is not None:
            ancestors.append(current)
            current = current.get_parent_location()
    
        return ancestors