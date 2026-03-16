from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from .models import User, Role
from .serializers import (
    UserMeSerializer,
    CustomerRegisterSerializer,
    WorkerRegisterSerializer,
    WorkerListSerializer,
    WorkerUpdateSerializer,
)
from .permissions import IsHR


class LoginView(TokenObtainPairView):
    """POST /api/accounts/login/"""
    pass


class TokenRefreshAPIView(TokenRefreshView):
    """POST /api/accounts/token/refresh/"""
    pass


class LogoutView(APIView):
    """POST /api/accounts/logout/ — blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/accounts/me/"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user


class CustomerRegisterView(generics.CreateAPIView):
    """POST /api/accounts/register/ — самостійна реєстрація клієнта."""
    permission_classes = [AllowAny]
    serializer_class = CustomerRegisterSerializer


class WorkerListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/accounts/workers/ — HR: список і реєстрація працівників."""
    permission_classes = [IsHR]

    def get_queryset(self):
        qs = User.objects.exclude(role__in=[Role.CUSTOMER, Role.ADMIN]).order_by('-date_joined')
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
            Q(last_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(username__icontains=search)
            )
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkerRegisterSerializer
        return WorkerListSerializer


class WorkerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/accounts/workers/<id>/ — HR: деталі/редагування/деактивація."""
    permission_classes = [IsHR]
    queryset = User.objects.exclude(role__in=[Role.CUSTOMER, Role.ADMIN])

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return WorkerUpdateSerializer
        return WorkerListSerializer

    def destroy(self, request, *args, **kwargs):
        """Не видаляємо — деактивуємо."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'detail': 'Користувача деактивовано.'}, status=status.HTTP_200_OK)
