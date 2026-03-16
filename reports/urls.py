from django.urls import path
from .views import (
    ShipmentBarcodePDF, ShipmentReceiptPDF, ShipmentDeliveryPDF, ShipmentPaymentPDF,
    DispatchDepartPDF, DispatchArrivePDF, LocationReportPDF,
)

urlpatterns = [
    path('shipment/<int:pk>/barcode/', ShipmentBarcodePDF.as_view()),
    path('shipment/<int:pk>/receipt/', ShipmentReceiptPDF.as_view()),
    path('shipment/<int:pk>/delivery/', ShipmentDeliveryPDF.as_view()),
    path('shipment/<int:pk>/payment/', ShipmentPaymentPDF.as_view()),
    path('dispatch/<int:pk>/depart/', DispatchDepartPDF.as_view()),
    path('dispatch/<int:pk>/arrive/', DispatchArrivePDF.as_view()),
    path('location/', LocationReportPDF.as_view()),
]
