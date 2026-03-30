from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Location, LocationType
from .serializers import LocationSerializer


from rest_framework.generics import ListAPIView

class LocationListView(ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Location.objects.filter(is_active=True).select_related('city')

        loc_type = self.request.query_params.get('type')
        city = self.request.query_params.get('city')
        q = self.request.query_params.get('q')

        if loc_type:
            qs = qs.filter(type=loc_type)

        if city:
            qs = qs.filter(city__name__icontains=city)

        if q:
            qs = qs.filter(name__icontains=q)

        return qs.order_by('name')


class LocationDetailView(generics.RetrieveAPIView):
    """GET /api/locations/<id>/"""
    permission_classes = [IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
