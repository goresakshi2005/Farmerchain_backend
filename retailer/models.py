from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from common.models import BaseBid
from fpo.models import FPOQuoteRequest

class Retailer(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    gstin = models.CharField(max_length=15, unique=True)
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


class RetailerBid(BaseBid):
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='bids')
    quote = models.ForeignKey(FPOQuoteRequest, on_delete=models.CASCADE, related_name='bids')

    def __str__(self):
        return f"Bid by {self.retailer.name} for {self.quote.product_name}"