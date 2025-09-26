from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from utils.carbon_calculator import CarbonEmissionsCalculator

class CarbonFootprintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        required_fields = ['start_addr', 'end_addr', 'vehicle_type']
        if not all(field in data for field in required_fields):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        calculator = CarbonEmissionsCalculator()
        result = calculator.calculate_road_emissions(
            start_addr=data['start_addr'],
            end_addr=data['end_addr'],
            vehicle_type=data['vehicle_type'],
            vehicle_count=int(data.get('vehicle_count', 1)),
            load_percentage=int(data.get('load_percentage', 100)),
            empty_return=bool(data.get('empty_return', False))
        )
        
        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)