from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import RegisterAPIView, MeAPIView, UserListAPIView, UserRoleUpdateAPIView
from .views import profile_view

urlpatterns = [
    # สมัครสมาชิก
    path('auth/register/', RegisterAPIView.as_view(), name='auth-register'),

    # JWT Login & Refresh
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ข้อมูล user ปัจจุบัน
    path('auth/me/', MeAPIView.as_view(), name='auth-me'),

    # Admin: ดู user ทั้งหมด + เปลี่ยน role
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('users/<int:pk>/role/', UserRoleUpdateAPIView.as_view(), name='user-role-update'),
    # Profile page (template)
    path('account/profile/', profile_view, name='account_profile'),
]
