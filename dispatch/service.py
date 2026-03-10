from django.core.exceptions import ValidationError
from logistics.services import build_route
from locations.models import Location


def get_next_hop_location(shipment, current_location: Location) -> Location | None:
    """
    Повертає наступну локацію по маршруту для конкретної посилки відносно current_location.
    Якщо current_location = остання точка — повертає None.
    """
    route = build_route(shipment.origin, shipment.destination)

    idx = None
    for i, loc in enumerate(route):
        if loc.id == current_location.id:
            idx = i
            break

    if idx is None:
        raise ValidationError("Current location is not in computed route.")

    if idx + 1 >= len(route):
        return None

    return route[idx + 1]
