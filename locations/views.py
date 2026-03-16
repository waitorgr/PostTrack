from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Location, LocationType
from .serializers import LocationSerializer


class LocationListView(generics.ListAPIView):
    """GET /api/locations/ — всі активні локації."""
    permission_classes = [AllowAny]
    serializer_class = LocationSerializer

    def get_queryset(self):
        qs = Location.objects.filter(is_active=True)
        loc_type = self.request.query_params.get('type')
        city = self.request.query_params.get('city')
        if loc_type:
            qs = qs.filter(type=loc_type)
        if city:
            qs = qs.filter(city__icontains=city)
        return qs


class LocationDetailView(generics.RetrieveAPIView):
    """GET /api/locations/<id>/"""
    permission_classes = [IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
