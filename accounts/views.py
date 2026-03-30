from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Role, User
from .permissions import CanViewDriversForRouting, IsHR
from .serializers import (
    CustomerRegisterSerializer,
    DriverOptionSerializer,
    UserMeSerializer,
    WorkerListSerializer,
    WorkerRegisterSerializer,
    WorkerUpdateSerializer,
)


class LoginView(TokenObtainPairView):
    """POST /api/accounts/login/"""
    pass


class TokenRefreshAPIView(TokenRefreshView):
    """POST /api/accounts/token/refresh/"""
    pass


class LogoutView(APIView):
    """POST /api/accounts/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": 'Поле "refresh" є обов’язковим.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Недійсний або прострочений refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Не вдалося виконати logout для цього refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Вихід виконано."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/accounts/me/"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user


class CustomerRegisterView(generics.CreateAPIView):
    """POST /api/accounts/register/"""
    permission_classes = [AllowAny]
    serializer_class = CustomerRegisterSerializer


class WorkerListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/accounts/workers/"""
    permission_classes = [IsHR]

    def get_queryset(self):
        qs = (
            User.objects
            .exclude(role__in=[Role.CUSTOMER, Role.ADMIN])
            .select_related("location", "region")
            .order_by("-date_joined")
        )

        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(last_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(patronymic__icontains=search)
                | Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkerRegisterSerializer
        return WorkerListSerializer


class WorkerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/accounts/workers/<id>/"""
    permission_classes = [IsHR]
    queryset = (
        User.objects
        .exclude(role__in=[Role.CUSTOMER, Role.ADMIN])
        .select_related("location", "region")
    )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return WorkerUpdateSerializer
        return WorkerListSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        User.objects.filter(pk=user.pk).update(is_active=False)
        return Response(
            {"detail": "Користувача деактивовано."},
            status=status.HTTP_200_OK,
        )


class DriverListView(generics.ListAPIView):
    """
    Окремий endpoint тільки для вибору водіїв логістом.
    Не відкриває повний список працівників.
    """
    permission_classes = [CanViewDriversForRouting]
    serializer_class = DriverOptionSerializer

    def get_queryset(self):
        qs = (
            User.objects
            .filter(role=Role.DRIVER, is_active=True)
            .select_related("location", "region")
            .order_by("first_name", "last_name", "username")
        )

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(last_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(patronymic__icontains=search)
                | Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        return qs