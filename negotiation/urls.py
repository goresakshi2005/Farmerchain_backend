from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NegotiationViewSet

router = DefaultRouter()
router.register(r'', NegotiationViewSet, basename='negotiation')

urlpatterns = [
    path('', include(router.urls)),
]