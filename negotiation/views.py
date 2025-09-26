from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from .models import Negotiation, NegotiationMessage
from .serializers import NegotiationSerializer, NegotiationMessageSerializer
from fpo.models import FPOBid
from retailer.models import RetailerBid

class NegotiationViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage negotiations.
    A user can view negotiations they are a part of, send messages, and accept/reject.
    """
    serializer_class = NegotiationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Q objects to find negotiations where the user is either the bidder or the quote owner
        fpo_bid_type = ContentType.objects.get_for_model(FPOBid)
        retailer_bid_type = ContentType.objects.get_for_model(RetailerBid)

        # User is the bidder (FPO or Retailer)
        is_fpo_bidder = Q(content_type=fpo_bid_type, bid_fpo__id=user.id)
        is_retailer_bidder = Q(content_type=retailer_bid_type, bid_retailer__id=user.id)
        
        # User is the quote owner (Farmer or FPO)
        is_farmer_quote_owner = Q(content_type=fpo_bid_type, bid_fpo__quote__farmer__id=user.id)
        is_fpo_quote_owner = Q(content_type=retailer_bid_type, bid_retailer__quote__fpo__id=user.id)

        return Negotiation.objects.filter(
            (is_fpo_bidder | is_retailer_bidder | is_farmer_quote_owner | is_fpo_quote_owner)
        ).distinct()

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        negotiation = self.get_object()
        
        if negotiation.status != 'active':
            return Response({'error': 'This negotiation is not active.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                negotiation=negotiation,
                sender_role=request.user.role,
                sender_id=request.user.id,
                sender_name=request.user.name
            )
            # Add email notification logic here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        negotiation = self.get_object()
        bid = negotiation.bid
        
        # Check if the user is the owner of the original quote
        is_owner = False
        if isinstance(bid, FPOBid) and request.user.id == bid.quote.farmer.id:
            is_owner = True
        if isinstance(bid, RetailerBid) and request.user.id == bid.quote.fpo.id:
            is_owner = True

        if not is_owner:
            return Response({'error': 'Only the quote owner can accept a negotiation.'}, status=status.HTTP_403_FORBIDDEN)
        
        negotiation.status = 'accepted'
        negotiation.save()
        
        bid.status = 'accepted'
        bid.save()
        
        bid.quote.status = 'awarded'
        bid.quote.accepted_bid = bid
        bid.quote.save()
        
        # Reject other bids for the same quote
        bid_model = bid.__class__
        bid_model.objects.filter(quote=bid.quote).exclude(id=bid.id).update(status='rejected')

        return Response({'status': 'Negotiation accepted and bid awarded.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        negotiation = self.get_object()
        negotiation.status = 'rejected'
        negotiation.save()
        
        negotiation.bid.status = 'rejected'
        negotiation.bid.save()
        
        return Response({'status': 'Negotiation rejected.'})