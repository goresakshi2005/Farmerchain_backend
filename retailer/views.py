from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from .models import Retailer, RetailerBid
from .serializers import RetailerSerializer, RetailerRegistrationSerializer, RetailerBidSerializer
from common.permissions import IsRetailer
from fpo.models import FPOQuoteRequest
from fpo.serializers import FPOQuoteRequestSerializer


class RetailerRegistrationView(generics.CreateAPIView):
    queryset = Retailer.objects.all()
    serializer_class = RetailerRegistrationSerializer
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
def retailer_login_check(request):
    email = request.data.get('email')
    
    try:
        retailer = Retailer.objects.get(email=email)
        if retailer.approval_status == 'pending':
            return Response({
                'message': 'Your account is pending admin approval. Please wait for approval to login.',
                'approved': False,
                'status': 'pending'
            }, status=status.HTTP_200_OK)
        elif retailer.approval_status == 'rejected':
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
    except Retailer.DoesNotExist:
        return Response({
            'message': 'Retailer not found with this email.',
            'approved': False,
            'status': 'not_found'
        }, status=status.HTTP_404_NOT_FOUND)


class RetailerListView(generics.ListAPIView):
    queryset = Retailer.objects.all()
    serializer_class = RetailerSerializer
    permission_classes = [IsAuthenticated, IsRetailer]


class RetailerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Retailer.objects.all()
    serializer_class = RetailerSerializer
    permission_classes = [IsAuthenticated, IsRetailer]


class OpenFPOQuotesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A view for Retailers to see and bid on open quotes from FPOs.
    """
    queryset = FPOQuoteRequest.objects.filter(status='open')
    serializer_class = FPOQuoteRequestSerializer
    permission_classes = [IsRetailer]

    @action(detail=True, methods=['post'], url_path='submit-bid')
    def submit_bid(self, request, pk=None):
        quote = self.get_object()
        retailer = Retailer.objects.get(id=request.user.id)

        # Check if retailer has already bid on this quote
        if RetailerBid.objects.filter(quote=quote, retailer=retailer).exists():
            return Response(
                {'error': 'You have already submitted a bid for this quote.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RetailerBidSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(retailer=retailer, quote=quote)
            # Add email notification logic here if needed
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)