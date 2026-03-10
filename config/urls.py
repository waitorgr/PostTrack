from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/locations/", include("locations.urls")),
    path("api/shipments/", include("shipments.urls")),
    path("api/tracking/", include("tracking.urls")),
    path("api/dispatch/", include("dispatch.urls")),
    path("api/logistics/", include("logistics.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
