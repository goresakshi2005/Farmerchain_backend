from .views import FPORegistrationView, FPOListView, FPODetailView, fpo_login_check, OpenFarmerQuotesViewSet, FPOQuoteRequestViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'farmer-quotes', OpenFarmerQuotesViewSet, basename='open-farmer-quote')
router.register(r'quotes', FPOQuoteRequestViewSet, basename='fpo-quote')

urlpatterns = [
    path('register/', FPORegistrationView.as_view(), name='fpo-register'),
    path('login-check/', fpo_login_check, name='fpo-login-check'),
    path('', FPOListView.as_view(), name='fpo-list'),
    path('<int:pk>/', FPODetailView.as_view(), name='fpo-detail'),
    path('', include(router.urls)),
]

