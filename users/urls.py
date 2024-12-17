
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    admin_view,
    manager_dashboard,
    employee_dashboard,
    UserViewSet,
)
from django.views.generic import TemplateView

# Initialize Router for the UserViewSets
router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    # Admin Site
    path('admin/', admin.site.urls),

    # API Endpoints
    path('users/api/register/', RegisterView.as_view(), name='api-register'),
    path('api/login/', LoginView.as_view(), name='api-login'),
    path('users/api/admin-page/', admin_view, name='api-admin-view'),
    path('users/api/manager-dashboard/', manager_dashboard, name='api-manager-dashboard'),
    path('users/api/employee-dashboard/', employee_dashboard, name='api-employee-dashboard'),
    path('users/api/', include(router.urls)),

]