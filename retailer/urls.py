
from .views import RetailerRegistrationView, RetailerListView, RetailerDetailView, retailer_login_check, OpenFPOQuotesViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'fpo-quotes', OpenFPOQuotesViewSet, basename='open-fpo-quote')

urlpatterns = [
    path('register/', RetailerRegistrationView.as_view(), name='retailer-register'),
    path('login-check/', retailer_login_check, name='retailer-login-check'),
    path('', RetailerListView.as_view(), name='retailer-list'),
    path('<int:pk>/', RetailerDetailView.as_view(), name='retailer-detail'),
    path('', include(router.urls)),
]