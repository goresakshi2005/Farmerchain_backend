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
        
        # Get ContentType for our Bid models
        fpo_bid_type = ContentType.objects.get_for_model(FPOBid)
        retailer_bid_type = ContentType.objects.get_for_model(RetailerBid)

        # 1. Find all FPO Bids where the current user is either the FPO (bidder) or the Farmer (quote owner)
        involved_fpo_bid_ids = FPOBid.objects.filter(
            Q(fpo_id=user.id) | Q(quote__farmer_id=user.id)
        ).values_list('id', flat=True)

        # 2. Find all Retailer Bids where the current user is either the Retailer (bidder) or the FPO (quote owner)
        involved_retailer_bid_ids = RetailerBid.objects.filter(
            Q(retailer_id=user.id) | Q(quote__fpo_id=user.id)
        ).values_list('id', flat=True)
        
        # 3. Build a query for Negotiations that point to any of these bids
        fpo_negotiations_query = Q(content_type=fpo_bid_type, object_id__in=list(involved_fpo_bid_ids))
        retailer_negotiations_query = Q(content_type=retailer_bid_type, object_id__in=list(involved_retailer_bid_ids))
        
        # 4. Combine the queries and return the final queryset
        return Negotiation.objects.filter(fpo_negotiations_query | retailer_negotiations_query).distinct()

    # ... (the rest of the view remains the same) ...

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        negotiation = self.get_object()
        bid = negotiation.bid
        
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