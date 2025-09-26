from django.urls import path
from .views import CarbonFootprintView

urlpatterns = [
    path('calculate-carbon/', CarbonFootprintView.as_view(), name='calculate-carbon'),
]