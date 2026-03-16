from .models import Route, RouteStep
from locations.models import Location, LocationType


class RouteService:

    @staticmethod
    def generate_route(shipment) -> Route:
        """
        Автоматична генерація маршруту:
          origin_post → sorting_center → distribution_center → sorting_center → destination_post
        """
        origin = shipment.origin_location
        dest   = shipment.destination_location

        sc_origin = (
            Location.objects.filter(type=LocationType.SORTING_CENTER, is_active=True).first()
        )
        dc = (
            Location.objects.filter(type=LocationType.DISTRIBUTION_CENTER, is_active=True).first()
        )
        sc_dest = (
            Location.objects.filter(type=LocationType.SORTING_CENTER, is_active=True).last()
        )

        route = Route.objects.create(shipment=shipment, is_custom=False)

        # Будуємо унікальний список кроків
        steps = [origin]
        if sc_origin and sc_origin != origin:
            steps.append(sc_origin)
        if dc and dc not in steps:
            steps.append(dc)
        if sc_dest and sc_dest not in steps and sc_dest != dest:
            steps.append(sc_dest)
        if dest not in steps:
            steps.append(dest)

        for i, location in enumerate(steps, start=1):
            RouteStep.objects.create(route=route, order=i, location=location)

        return route

    @staticmethod
    def update_route(route: Route, location_ids: list, updated_by) -> Route:
        """Логіст змінює маршрут вручну."""
        route.steps.all().delete()
        route.is_custom = True
        route.save()

        for i, loc_id in enumerate(location_ids, start=1):
            RouteStep.objects.create(route=route, order=i, location_id=loc_id)

        from tracking.services import TrackingService
        TrackingService.add_event(
            shipment=route.shipment,
            event_type="in_transit",
            location=route.shipment.current_location,
            performed_by=updated_by,
            note="Маршрут змінено логістом.",
            is_public=False,
        )
        return route
