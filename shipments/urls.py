from rest_framework.routers import DefaultRouter
from .views import ShipmentViewSet

router = DefaultRouter()
router.register(r"", ShipmentViewSet, basename="shipments")

urlpatterns = router.urls
