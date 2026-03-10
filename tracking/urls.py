from rest_framework.routers import DefaultRouter
from .views import TrackingEventViewSet

router = DefaultRouter()
router.register(r"", TrackingEventViewSet, basename="tracking")

urlpatterns = router.urls
