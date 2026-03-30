from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    CUSTOMER = "customer", "Клієнт"
    POSTAL_WORKER = "postal_worker", "Працівник відділення"
    SORTING_CENTER_WORKER = "sorting_center_worker", "Працівник сортувального центру"
    DISTRIBUTION_CENTER_WORKER = "distribution_center_worker", "Працівник розподільчого центру"
    DRIVER = "driver", "Водій"
    LOGIST = "logist", "Логіст"
    HR = "hr", "HR"
    ADMIN = "admin", "Адміністратор"


class User(AbstractUser):
    role = models.CharField(
        max_length=40,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    patronymic = models.CharField("По-батькові", max_length=150)
    phone = models.CharField("Телефон", max_length=20)

    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )

    region = models.ForeignKey(
        "locations.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logists",
    )

    REQUIRED_FIELDS = ["email", "first_name", "last_name", "patronymic", "phone", "role"]

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

    @property
    def is_employee(self):
        return self.role != Role.CUSTOMER

    @property
    def is_logistics_staff(self):
        return self.role in (Role.DRIVER, Role.LOGIST)

    @property
    def is_facility_worker(self):
        return self.role in (
            Role.POSTAL_WORKER,
            Role.SORTING_CENTER_WORKER,
            Role.DISTRIBUTION_CENTER_WORKER,
        )

    def is_role(self, *roles):
        return self.role in roles

    def clean(self):
        super().clean()

        from locations.models import LocationType

        errors = {}

        self.email = (self.email or "").strip().lower()
        self.phone = (self.phone or "").strip()

        if self.phone:
            if not self.phone.startswith("+380") or len(self.phone) != 13 or not self.phone[1:].isdigit():
                errors["phone"] = "Формат телефону: +380XXXXXXXXX"

        location_type_by_role = {
            Role.POSTAL_WORKER: LocationType.POST_OFFICE,
            Role.SORTING_CENTER_WORKER: LocationType.SORTING_CENTER,
            Role.DISTRIBUTION_CENTER_WORKER: LocationType.DISTRIBUTION_CENTER,
        }

        location_required_roles = {
            Role.POSTAL_WORKER,
            Role.SORTING_CENTER_WORKER,
            Role.DISTRIBUTION_CENTER_WORKER,
            Role.DRIVER,
        }

        no_location_roles = {
            Role.CUSTOMER,
            Role.LOGIST,
            Role.HR,
            Role.ADMIN,
        }

        no_region_roles = {
            Role.CUSTOMER,
            Role.POSTAL_WORKER,
            Role.SORTING_CENTER_WORKER,
            Role.DISTRIBUTION_CENTER_WORKER,
            Role.DRIVER,
            Role.HR,
            Role.ADMIN,
        }

        if self.role in location_required_roles and not self.location:
            errors["location"] = "Для цієї ролі потрібно вказати локацію."

        if self.role == Role.LOGIST and not self.region:
            errors["region"] = "Для ролі логіста потрібно вказати регіон."

        if self.role in no_location_roles and self.location:
            errors["location"] = "Для цієї ролі локація не повинна бути вказана."

        if self.role in no_region_roles and self.region:
            errors["region"] = "Для цієї ролі регіон не повинен бути вказаний."

        if self.role in location_type_by_role and self.location:
            expected_type = location_type_by_role[self.role]
            if self.location.type != expected_type:
                role_labels = {
                    Role.POSTAL_WORKER: "Працівник відділення",
                    Role.SORTING_CENTER_WORKER: "Працівник сортувального центру",
                    Role.DISTRIBUTION_CENTER_WORKER: "Працівник розподільчого центру",
                }
                location_labels = {
                    LocationType.POST_OFFICE: "поштове відділення",
                    LocationType.SORTING_CENTER: "сортувальний центр",
                    LocationType.DISTRIBUTION_CENTER: "розподільчий центр",
                }
                errors["location"] = (
                    f"{role_labels[self.role]} повинен бути прив'язаний до локації типу "
                    f"'{location_labels[expected_type]}'."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)