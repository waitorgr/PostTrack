from django.urls import path
from .views import PublicTrackingView, ShipmentEventsView

urlpatterns = [
    path('public/<str:tracking_number>/', PublicTrackingView.as_view()),
    path('events/', ShipmentEventsView.as_view()),
]
