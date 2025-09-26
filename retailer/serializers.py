from rest_framework import serializers
from .models import Retailer, RetailerBid


class RetailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

class RetailerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ['name', 'email', 'password', 'gstin', 'wallet_address', 'city', 'state']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        retailer = Retailer.objects.create(**validated_data)
        retailer.set_password(password)
        retailer.save()
        return retailer


class RetailerBidSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating a Retailer's bid.
    """
    class Meta:
        model = RetailerBid
        fields = [
            'id', 'bid_amount', 'delivery_time', 'comments', 
            'transport_mode', 'vehicle_type', 'submitted_at', 'status'
        ]
        read_only_fields = ['retailer', 'status', 'quote', 'submitted_at']

class RetailerBidDetailSerializer(RetailerBidSerializer):
    """
    Detailed serializer for viewing a bid, includes nested Retailer info.
    """
    retailer = RetailerSerializer(read_only=True)

    class Meta(RetailerBidSerializer.Meta):
        fields = RetailerBidSerializer.Meta.fields + ['retailer']