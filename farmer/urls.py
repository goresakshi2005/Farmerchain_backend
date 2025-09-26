from django.urls import path, include
from .views import FarmerRegistrationView, FarmerListView, FarmerDetailView, farmer_login_check, FarmerQuoteRequestViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'quotes', FarmerQuoteRequestViewSet, basename='farmer-quote')

urlpatterns = [
    path('register/', FarmerRegistrationView.as_view(), name='farmer-register'),
    path('login-check/', farmer_login_check, name='farmer-login-check'),
    path('', FarmerListView.as_view(), name='farmer-list'),
    path('<int:pk>/', FarmerDetailView.as_view(), name='farmer-detail'),
    path('', include(router.urls)),
]