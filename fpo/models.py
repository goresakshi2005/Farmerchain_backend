from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from common.models import BaseQuoteRequest, BaseBid
from farmer.models import Farmer, FarmerQuoteRequest

class FPO(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    corporate_identification_number = models.CharField(max_length=21, unique=True)
    wallet_address = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class FPOQuoteRequest(BaseQuoteRequest):
    fpo = models.ForeignKey(FPO, on_delete=models.CASCADE, related_name='quotes')
    accepted_bid = models.OneToOneField(
        'retailer.RetailerBid', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_for_quote'
    )
    
    def __str__(self):
        return f"{self.product_name} by {self.fpo.name}"

class FPOBid(BaseBid):
    fpo = models.ForeignKey(FPO, on_delete=models.CASCADE, related_name='bids')
    quote = models.ForeignKey(FarmerQuoteRequest, on_delete=models.CASCADE, related_name='bids')
    
    def __str__(self):
        return f"Bid by {self.fpo.name} for {self.quote.product_name}"