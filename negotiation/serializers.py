from rest_framework import serializers
from .models import Negotiation, NegotiationMessage
from fpo.serializers import FPOBidDetailSerializer
from retailer.serializers import RetailerBidDetailSerializer
from fpo.models import FPOBid
from retailer.models import RetailerBid

class GenericRelatedField(serializers.Field):
    """A custom field to handle generic relationships."""
    def to_representation(self, value):
        if isinstance(value, FPOBid):
            return FPOBidDetailSerializer(value).data
        if isinstance(value, RetailerBid):
            return RetailerBidDetailSerializer(value).data
        raise Exception('Unexpected type of tagged object')

class NegotiationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationMessage
        fields = '__all__'
        read_only_fields = ['negotiation', 'sender_role', 'sender_id', 'sender_name']

class NegotiationSerializer(serializers.ModelSerializer):
    bid = GenericRelatedField(read_only=True)
    messages = NegotiationMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Negotiation
        fields = ['id', 'status', 'created_at', 'bid', 'messages']