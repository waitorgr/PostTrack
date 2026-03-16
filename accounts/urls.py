from django.urls import path
from .views import (
    LoginView, TokenRefreshAPIView, LogoutView,
    MeView, CustomerRegisterView,
    WorkerListCreateView, WorkerDetailView,
)

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('token/refresh/', TokenRefreshAPIView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('me/', MeView.as_view()),
    path('register/', CustomerRegisterView.as_view()),
    path('workers/', WorkerListCreateView.as_view()),
    path('workers/<int:pk>/', WorkerDetailView.as_view()),
]
