from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from locations.models import Location, LocationType


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    HR = "hr", "HR"
    POSTAL_WORKER = "postal_worker", "Postal worker"
    WAREHOUSE_WORKER = "warehouse_worker", "Warehouse worker"
    LOGIST = "logist", "Logist"
    DRIVER = "driver", "Driver"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.CUSTOMER)

    assigned_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_users",
    )

    def clean(self):
        super().clean()

        # CUSTOMER — без прив’язки
        if self.role == UserRole.CUSTOMER:
            return

        # POSTAL_WORKER — тільки POST_OFFICE
        if self.role == UserRole.POSTAL_WORKER:
            if not self.assigned_location:
                raise ValidationError({"assigned_location": "Postal worker must have assigned post office."})
            if self.assigned_location.type != LocationType.POST_OFFICE:
                raise ValidationError({"assigned_location": "Postal worker must be assigned to a Post Office."})

        # WAREHOUSE_WORKER — SC або DC
        if self.role == UserRole.WAREHOUSE_WORKER:
            if not self.assigned_location:
                raise ValidationError({"assigned_location": "Warehouse worker must have assigned SC/DC."})
            if self.assigned_location.type not in (LocationType.SORTING_CITY, LocationType.DISTRIBUTION_CENTER):
                raise ValidationError({"assigned_location": "Warehouse worker must be assigned to Sorting City or Distribution Center."})

        # LOGIST/DRIVER/HR/ADMIN — можна без assigned_location (за бажанням)
