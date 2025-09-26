from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class BaseQuoteRequest(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('awarded', 'Awarded'), ('closed', 'Closed')]
    
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-deadline']

class BaseBid(models.Model):
    STATUS_CHOICES = [('submitted', 'Submitted'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]
    TRANSPORT_CHOICES = [('road', 'Road'), ('air', 'Air')]
    VEHICLE_CHOICES = [
        ('small_truck', 'Small Truck'), ('medium_truck', 'Medium Truck'),
        ('large_truck', 'Large Truck'), ('articulated_truck', 'Articulated Truck')
    ]

    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField(help_text="In days")
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)

    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='road')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, blank=True, null=True)
    
    class Meta:
        abstract = True
        ordering = ['-submitted_at']