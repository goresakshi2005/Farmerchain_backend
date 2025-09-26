
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from common.permissions import IsFPO

from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from .models import FPO, FPOQuoteRequest, FPOBid
from .serializers import FPOSerializer, FPORegistrationSerializer, FPOQuoteRequestSerializer, FPOBidSerializer
from farmer.models import FarmerQuoteRequest
from farmer.serializers import FarmerQuoteRequestSerializer
from retailer.models import RetailerBid
from retailer.serializers import RetailerBidDetailSerializer



class FPORegistrationView(generics.CreateAPIView):
    queryset = FPO.objects.all()
    serializer_class = FPORegistrationSerializer
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
def fpo_login_check(request):
    email = request.data.get('email')
    
    try:
        fpo = FPO.objects.get(email=email)
        if fpo.approval_status == 'pending':
            return Response({
                'message': 'Your account is pending admin approval. Please wait for approval to login.',
                'approved': False,
                'status': 'pending'
            }, status=status.HTTP_200_OK)
        elif fpo.approval_status == 'rejected':
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
    except FPO.DoesNotExist:
        return Response({
            'message': 'FPO not found with this email.',
            'approved': False,
            'status': 'not_found'
        }, status=status.HTTP_404_NOT_FOUND)


class FPOListView(generics.ListAPIView):
    queryset = FPO.objects.all()
    serializer_class = FPOSerializer
    permission_classes = [IsAuthenticated, IsFPO]


class FPODetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FPO.objects.all()
    serializer_class = FPOSerializer
    permission_classes = [IsAuthenticated, IsFPO]



class OpenFarmerQuotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FarmerQuoteRequest.objects.filter(status='open')
    serializer_class = FarmerQuoteRequestSerializer
    permission_classes = [IsFPO]

    @action(detail=True, methods=['post'], url_path='submit-bid')
    def submit_bid(self, request, pk=None):
        quote = self.get_object()
        fpo = FPO.objects.get(id=request.user.id)
        
        serializer = FPOBidSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(fpo=fpo, quote=quote)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# For FPOs to manage their own quotes for Retailers
class FPOQuoteRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FPOQuoteRequestSerializer
    permission_classes = [IsFPO]

    def get_queryset(self):
        fpo = FPO.objects.get(id=self.request.user.id)
        return FPOQuoteRequest.objects.filter(fpo=fpo)

    def perform_create(self, serializer):
        fpo = FPO.objects.get(id=self.request.user.id)
        serializer.save(fpo=fpo)

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        quote = self.get_object()
        bids = RetailerBid.objects.filter(quote=quote)
        serializer = RetailerBidDetailSerializer(bids, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='accept-bid')
    def accept_bid(self, request, pk=None):
        # ... logic similar to Farmer's accept_bid view ...
        pass