from rest_framework.routers import DefaultRouter
from .views import DispatchGroupViewSet

router = DefaultRouter()
router.register(r"groups", DispatchGroupViewSet, basename="dispatch-groups")

urlpatterns = router.urls
