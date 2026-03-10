from django.core.exceptions import ValidationError
from django.db import models, transaction
from core.models import TimeStampedModel


class LocationType(models.TextChoices):
    DISTRIBUTION_CENTER = "distribution_center", "Distribution center"  # область
    SORTING_CITY = "sorting_city", "Sorting city"                       # район
    POST_OFFICE = "post_office", "Post office"                          # відділення


class Location(TimeStampedModel):
    type = models.CharField(max_length=32, choices=LocationType.choices)

    # DC: 2 digits (01..99)
    # SC: 4 digits (0101..9999) = DC(2) + district(2)
    # PO: 9 digits (010100001) = SC(4) + office(5)
    code = models.CharField(max_length=9, unique=True, blank=True, editable=False)

    # SC -> DC
    parent_dc = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sorting_cities",
        limit_choices_to={"type": LocationType.DISTRIBUTION_CENTER},
    )

    # PO -> SC
    parent_sc = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="post_offices",
        limit_choices_to={"type": LocationType.SORTING_CITY},
    )

    name = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)

    def clean(self):
        # ---- Зв'язки ----
        if self.type == LocationType.DISTRIBUTION_CENTER:
            if self.parent_dc or self.parent_sc:
                raise ValidationError("Distribution Center cannot have parent_dc/parent_sc.")

        if self.type == LocationType.SORTING_CITY:
            if not self.parent_dc:
                raise ValidationError({"parent_dc": "Sorting city must be assigned to a Distribution Center."})
            if self.parent_sc:
                raise ValidationError({"parent_sc": "Sorting city cannot have parent_sc."})

        if self.type == LocationType.POST_OFFICE:
            if not self.parent_sc:
                raise ValidationError({"parent_sc": "Post office must be assigned to a Sorting City."})
            if self.parent_dc:
                raise ValidationError({"parent_dc": "Post office must NOT have parent_dc (use parent_sc -> parent_dc)."})

        # ---- Перевірка формату коду ----
        if self.code:
            if not self.code.isdigit():
                raise ValidationError({"code": "Code must be numeric."})

            if self.type == LocationType.DISTRIBUTION_CENTER:
                if len(self.code) != 2:
                    raise ValidationError({"code": "DC code must be exactly 2 digits (e.g. 01)."})

            if self.type == LocationType.SORTING_CITY:
                if len(self.code) != 4:
                    raise ValidationError({"code": "Sorting city code must be exactly 4 digits (e.g. 0101)."})
                if self.parent_dc and not self.code.startswith(self.parent_dc.code):
                    raise ValidationError({"code": "Sorting city code must start with parent DC code."})

            if self.type == LocationType.POST_OFFICE:
                if len(self.code) != 9:
                    raise ValidationError({"code": "Post office code must be exactly 9 digits (e.g. 010100001)."})
                if self.parent_sc and not self.code.startswith(self.parent_sc.code):
                    raise ValidationError({"code": "Post office code must start with parent SC code."})

    def _next_dc_code(self) -> str:
        last = (
            Location.objects.select_for_update()
            .filter(type=LocationType.DISTRIBUTION_CENTER)
            .order_by("-code")
            .first()
        )
        next_num = int(last.code) + 1 if last and last.code and last.code.isdigit() else 1
        if next_num > 99:
            raise ValidationError("DC code overflow: max 99.")
        return f"{next_num:02d}"

    def _next_sc_code(self) -> str:
        if not self.parent_dc:
            raise ValidationError("parent_dc is required for Sorting City code generation.")

        if not self.parent_dc.code:
            self.parent_dc.save()

        dc_prefix = self.parent_dc.code  # "01"
        last = (
            Location.objects.select_for_update()
            .filter(type=LocationType.SORTING_CITY, parent_dc=self.parent_dc, code__startswith=dc_prefix)
            .order_by("-code")
            .first()
        )
        last_suffix = int(last.code[-2:]) if last and last.code and last.code[-2:].isdigit() else 0
        next_suffix = last_suffix + 1
        if next_suffix > 99:
            raise ValidationError("Sorting city code overflow: max 99 per DC.")
        return f"{dc_prefix}{next_suffix:02d}"  # "0101"

    def _next_post_office_code(self) -> str:
        if not self.parent_sc:
            raise ValidationError("parent_sc is required for Post Office code generation.")

        if not self.parent_sc.code:
            self.parent_sc.save()

        sc_prefix = self.parent_sc.code  # "0101"
        last = (
            Location.objects.select_for_update()
            .filter(type=LocationType.POST_OFFICE, parent_sc=self.parent_sc, code__startswith=sc_prefix)
            .order_by("-code")
            .first()
        )
        last_suffix = int(last.code[-5:]) if last and last.code and last.code[-5:].isdigit() else 0
        next_suffix = last_suffix + 1
        if next_suffix > 99999:
            raise ValidationError("Post office code overflow: max 99999 per SC.")
        return f"{sc_prefix}{next_suffix:05d}"  # "010100001"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.code:
                # перевіряємо зв’язки (parent_*)
                self.full_clean()

                if self.type == LocationType.DISTRIBUTION_CENTER:
                    self.code = self._next_dc_code()
                elif self.type == LocationType.SORTING_CITY:
                    self.code = self._next_sc_code()
                else:
                    self.code = self._next_post_office_code()

            # Автоназіва
            if not (self.name or "").strip():
                if self.type == LocationType.POST_OFFICE:
                    i = int(self.code[-5:])  # 010100001 -> 1
                    self.name = f"Відділення {i}"
                elif self.type == LocationType.SORTING_CITY:
                    i = int(self.code[-2:])  # 0101 -> 1
                    self.name = f"Сортувальний центр {i}"
                elif self.type == LocationType.DISTRIBUTION_CENTER:
                    i = int(self.code)        # 01 -> 1
                    self.name = f"Розподільчий центр {i}"

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} | {self.name} ({self.type}) - {self.city}"
