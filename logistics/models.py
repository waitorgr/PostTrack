from django.conf import settings
from django.db import models
from core.models import TimeStampedModel
from locations.models import Location
from dispatch.models import DispatchGroup


class DriverType(models.TextChoices):
    REGIONAL = "regional", "Regional"
    INTERREGIONAL = "interregional", "Interregional"


class TripStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "Canceled"


class Truck(TimeStampedModel):
    plate_number = models.CharField(max_length=16, unique=True)
    model = models.CharField(max_length=64, blank=True)
    max_load_kg = models.DecimalField(max_digits=10, decimal_places=2)
    max_volume_m3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    last_service_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.plate_number} ({'available' if self.is_available else 'busy'})"


class RoutePlan(TimeStampedModel):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="route_plans")
    driver_type_required = models.CharField(max_length=20, choices=DriverType.choices, default=DriverType.REGIONAL)

    planned_start_at = models.DateTimeField()
    planned_end_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"RoutePlan #{self.id} ({self.driver_type_required})"


class RouteStop(TimeStampedModel):
    route_plan = models.ForeignKey(RoutePlan, on_delete=models.CASCADE, related_name="stops")
    sequence_number = models.PositiveIntegerField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    planned_arrival_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("route_plan", "sequence_number")
        ordering = ["sequence_number"]

    def __str__(self):
        return f"{self.route_plan_id} stop {self.sequence_number}: {self.location.code}"


def generate_trip_code(prefix="TRIP"):
    import random, string
    body = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{body}"


class Trip(TimeStampedModel):
    trip_code = models.CharField(max_length=32, unique=True, editable=False)

    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.PLANNED)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="trips_as_driver")
    truck = models.ForeignKey(Truck, on_delete=models.PROTECT, related_name="trips")
    route_plan = models.ForeignKey(RoutePlan, on_delete=models.PROTECT, related_name="trips")

    def save(self, *args, **kwargs):
        if not self.trip_code:
            code = generate_trip_code()
            while Trip.objects.filter(trip_code=code).exists():
                code = generate_trip_code()
            self.trip_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trip_code} ({self.status})"


class TripDispatchGroup(TimeStampedModel):
    """
    Партія = один переїзд from_location -> to_location, зазвичай належить одному рейсу.
    """
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="trip_groups")
    group = models.OneToOneField(DispatchGroup, on_delete=models.PROTECT, related_name="trip_link")
    sequence_number = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("trip", "sequence_number")
        ordering = ["sequence_number"]

    def __str__(self):
        return f"{self.trip.trip_code} -> {self.group.group_code}"
