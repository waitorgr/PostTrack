from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware

from accounts.permissions import IsPostalOrWarehouse, IsStaff
from shipments.models import Shipment
from dispatch.models import DispatchGroup
from .pdf_generator import (
    generate_shipment_receipt,
    generate_dispatch_depart_report,
    generate_dispatch_arrive_report,
    generate_delivery_report,
    generate_payment_report,
    generate_location_report,
)
from .barcode_generator import generate_barcode_pdf


class ShipmentBarcodePDF(APIView):
    """GET /api/reports/shipment/<id>/barcode/ - Окремий штрихкод"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        buffer = generate_barcode_pdf(shipment.tracking_number)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"barcode_{shipment.tracking_number}.pdf",
                            content_type='application/pdf')


class ShipmentReceiptPDF(APIView):
    """GET /api/reports/shipment/<id>/receipt/"""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        buffer = generate_shipment_receipt(shipment)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"receipt_{shipment.tracking_number}.pdf",
                            content_type='application/pdf')


class ShipmentDeliveryPDF(APIView):
    """GET /api/reports/shipment/<id>/delivery/"""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        buffer = generate_delivery_report(shipment, confirmed_by=request.user)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"delivery_{shipment.tracking_number}.pdf",
                            content_type='application/pdf')


class ShipmentPaymentPDF(APIView):
    """GET /api/reports/shipment/<id>/payment/"""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        buffer = generate_payment_report(shipment)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"payment_{shipment.tracking_number}.pdf",
                            content_type='application/pdf')


class DispatchDepartPDF(APIView):
    """GET /api/reports/dispatch/<id>/depart/"""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request, pk):
        group = get_object_or_404(DispatchGroup, pk=pk)
        buffer = generate_dispatch_depart_report(group, handed_by=request.user)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"dispatch_depart_{group.code}.pdf",
                            content_type='application/pdf')


class DispatchArrivePDF(APIView):
    """GET /api/reports/dispatch/<id>/arrive/"""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request, pk):
        group = get_object_or_404(DispatchGroup, pk=pk)
        buffer = generate_dispatch_arrive_report(group, received_by=request.user)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"dispatch_arrive_{group.code}.pdf",
                            content_type='application/pdf')


class LocationReportPDF(APIView):
    """GET /api/reports/location/ — загальний звіт по локації поточного користувача."""
    permission_classes = [IsPostalOrWarehouse]

    def get(self, request):
        user = request.user
        if not user.location:
            return Response({'detail': 'Не прив\'язано до локації.'}, status=400)

        from django.utils import timezone
        from datetime import timedelta
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        import datetime as dt
        if date_from_str:
            date_from = make_aware(dt.datetime.strptime(date_from_str, '%Y-%m-%d'))
        else:
            date_from = timezone.now() - timedelta(days=30)
        if date_to_str:
            date_to = make_aware(dt.datetime.strptime(date_to_str, '%Y-%m-%d'))
        else:
            date_to = timezone.now()

        shipments = Shipment.objects.filter(
            origin=user.location,
            created_at__range=(date_from, date_to),
        ).select_related('origin', 'destination', 'payment')

        dispatch_groups = DispatchGroup.objects.filter(
            origin=user.location,
            created_at__range=(date_from, date_to),
        ).select_related('destination').prefetch_related('items')

        buffer = generate_location_report(
            location=user.location,
            shipments=list(shipments),
            dispatch_groups=list(dispatch_groups),
            date_from=date_from,
            date_to=date_to,
        )
        return FileResponse(buffer, as_attachment=True,
                            filename=f"report_{user.location.code}.pdf",
                            content_type='application/pdf')
