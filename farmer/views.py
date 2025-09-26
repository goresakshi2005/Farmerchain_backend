from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Farmer
from .serializers import FarmerSerializer, FarmerRegistrationSerializer
from common.permissions import IsFarmer

from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import Farmer, FarmerQuoteRequest
from .serializers import FarmerSerializer, FarmerRegistrationSerializer, FarmerQuoteRequestSerializer
from fpo.models import FPOBid
from fpo.serializers import FPOBidDetailSerializer



class FarmerRegistrationView(generics.CreateAPIView):
    queryset = Farmer.objects.all()
    serializer_class = FarmerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Registration successful. Please wait for admin approval.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def farmer_login_check(request):
    email = request.data.get('email')
    
    try:
        farmer = Farmer.objects.get(email=email)
        if farmer.approval_status == 'pending':
            return Response({
                'message': 'Your account is pending admin approval. Please wait for approval to login.',
                'approved': False,
                'status': 'pending'
            }, status=status.HTTP_200_OK)
        elif farmer.approval_status == 'rejected':
            return Response({
                'message': 'Your account has been rejected by admin. Please contact support.',
                'approved': False,
                'status': 'rejected'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Account is approved. You can proceed to login.',
                'approved': True,
                'status': 'approved'
            }, status=status.HTTP_200_OK)
    except Farmer.DoesNotExist:
        return Response({
            'message': 'Farmer not found with this email.',
            'approved': False,
            'status': 'not_found'
        }, status=status.HTTP_404_NOT_FOUND)


class FarmerListView(generics.ListAPIView):
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated, IsFarmer]


class FarmerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated, IsFarmer]



class FarmerQuoteRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FarmerQuoteRequestSerializer
    permission_classes = [IsFarmer]

    def get_queryset(self):
        farmer = Farmer.objects.get(id=self.request.user.id)
        return FarmerQuoteRequest.objects.filter(farmer=farmer)

    def perform_create(self, serializer):
        farmer = Farmer.objects.get(id=self.request.user.id)
        serializer.save(farmer=farmer)

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        quote = self.get_object()
        bids = FPOBid.objects.filter(quote=quote)
        serializer = FPOBidDetailSerializer(bids, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='accept-bid')
    def accept_bid(self, request, pk=None):
        quote = self.get_object()
        bid_id = request.data.get('bid_id')
        
        if quote.status != 'open':
            return Response({'error': 'This quote is not open for bidding.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bid_to_accept = FPOBid.objects.get(id=bid_id, quote=quote)
            
            # Accept the bid and update statuses
            bid_to_accept.status = 'accepted'
            bid_to_accept.save()
            
            quote.accepted_bid = bid_to_accept
            quote.status = 'awarded'
            quote.save()

            # Reject other bids
            FPOBid.objects.filter(quote=quote).exclude(id=bid_id).update(status='rejected')

            return Response({'status': f'Bid {bid_id} accepted.'})
        except FPOBid.DoesNotExist:
            return Response({'error': 'Bid not found for this quote.'}, status=status.HTTP_404_NOT_FOUND)