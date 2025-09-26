import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import logging
from django.conf import settings
import math

logger = logging.getLogger(__name__)

class RouteFinder:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.OPENROUTE_API_KEY
        self.geolocator = Nominatim(user_agent="farmer_chain_app", timeout=10)
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)

    def get_coords(self, address):
        location = self.geocode(address)
        if not location:
            raise ValueError(f"Address not found: {address}")
        return (location.latitude, location.longitude)

    def calculate_route_details(self, start_addr, end_addr, transport_mode, lead_time_days):
        try:
            start_coords = self.get_coords(start_addr)
            end_coords = self.get_coords(end_addr)
            
            if transport_mode == 'road':
                headers = {"Authorization": self.api_key}
                body = {"coordinates": [start_coords[::-1], end_coords[::-1]]}
                
                response = requests.post(
                    "https://api.openrouteservice.org/v2/directions/driving-car",
                    json=body, headers=headers, timeout=15
                )
                response.raise_for_status()
                route_data = response.json()
                
                distance_km = route_data['routes'][0]['summary']['distance'] / 1000
                realistic_duration_hours = distance_km / 50  # Avg 50km/h
                total_days = float(lead_time_days) + (realistic_duration_hours / 24)
                
                return {
                    'success': True, 'mode': 'road',
                    'distance': round(distance_km, 1),
                    'delivery_days': math.ceil(total_days)
                }
            return None
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return None