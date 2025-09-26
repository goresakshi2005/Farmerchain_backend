from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from common.models import BaseQuoteRequest

class Farmer(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    aadhaar_number = models.CharField(max_length=12, unique=True)
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


class FarmerQuoteRequest(BaseQuoteRequest):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='quotes')
    accepted_bid = models.OneToOneField(
        'fpo.FPOBid', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_for_quote'
    )
    
    def __str__(self):
        return f"{self.product_name} by {self.farmer.name}"