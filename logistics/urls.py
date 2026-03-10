from rest_framework.routers import DefaultRouter
from .views import TruckViewSet, RoutePlanViewSet, RouteStopViewSet, TripViewSet, TripDispatchGroupViewSet

router = DefaultRouter()
router.register(r"trucks", TruckViewSet, basename="trucks")
router.register(r"route-plans", RoutePlanViewSet, basename="route-plans")
router.register(r"route-stops", RouteStopViewSet, basename="route-stops")
router.register(r"trips", TripViewSet, basename="trips")
router.register(r"trip-groups", TripDispatchGroupViewSet, basename="trip-groups")

urlpatterns = router.urls
