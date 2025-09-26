import requests
import logging
from django.conf import settings
from .route_calculator import RouteFinder

logger = logging.getLogger(__name__)

class CarbonEmissionsCalculator:
    EMISSION_FACTORS = {
        'small_truck': 250,
        'medium_truck': 400,
        'large_truck': 600,
        'articulated_truck': 900
    }

    def calculate_road_emissions(self, start_addr, end_addr, vehicle_type, vehicle_count=1, load_percentage=100, empty_return=False):
        try:
            route_finder = RouteFinder()
            route_details = route_finder.calculate_route_details(start_addr, end_addr, 'road', 0)
            
            if not route_details or not route_details.get('success'):
                raise ValueError("Could not calculate route distance")

            distance_km = route_details['distance']
            
            load_factor = load_percentage / 100
            emissions_grams = (self.EMISSION_FACTORS[vehicle_type] * distance_km * vehicle_count) / load_factor
            
            if empty_return:
                emissions_grams *= 2
                distance_km *= 2
            
            return {
                'success': True,
                'distance_km': round(distance_km, 2),
                'total_emissions_kg': round(emissions_grams / 1000, 2),
                'equivalent_trees': round(emissions_grams / 21000, 1)
            }
        except Exception as e:
            logger.error(f"Carbon calculation failed: {e}")
            return {'success': False, 'error': str(e)}