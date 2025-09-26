from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from fpo.models import FPO, FPOQuoteRequest
from .models import Retailer

class RetailerBidWorkflowTests(APITestCase):
    """
    Tests for the Retailer workflow: viewing FPO quotes and submitting bids.
    """
    def setUp(self):
        """
        Set up an FPO with a quote, and a Retailer to bid on it.
        """
        self.fpo = FPO.objects.create(
            name="Agri Corp", email="agri@corp.com", corporate_identification_number="CIN987654321",
            wallet_address="0xFPOAgriCorpWallet", city="Metro", state="Commerce",
            approval_status='approved'
        )
        self.fpo.set_password("fpopass")
        self.fpo.save()
        
        self.quote = FPOQuoteRequest.objects.create(
            fpo=self.fpo, product_name="Premium Rice", category="Grains",
            deadline="2025-11-15", quantity=1500, unit="kg", description="Aged Basmati Rice"
        )

        self.retailer = Retailer.objects.create(
            name="SuperMart", email="super@mart.com", gstin="GSTIN123456789",
            wallet_address="0xRetailerWallet", city="Cityville", state="Urban",
            approval_status='approved'
        )
        self.retailer.set_password("retailerpass")
        self.retailer.save()

        self.retailer_token = self.get_token('super@mart.com', 'retailerpass', 'retailer')

    def get_token(self, username, password, role):
        """Helper function to get JWT token."""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': username, 'password': password, 'role': role}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_retailer_can_view_open_fpo_quotes(self):
        """
        Ensure an authenticated retailer can see a list of open quotes from FPOs.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.retailer_token)
        url = reverse('open-fpo-quote-list')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.quote.id)
        self.assertEqual(response.data[0]['product_name'], "Premium Rice")

    def test_retailer_can_submit_bid(self):
        """
        Ensure an authenticated retailer can submit a valid bid to an open FPO quote.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.retailer_token)
        
        url = reverse('open-fpo-quote-submit-bid', kwargs={'pk': self.quote.id})
        
        bid_data = {
            "bid_amount": 25000.00,
            "delivery_time": 3,
            "comments": "Ready for immediate pickup.",
            "transport_mode": "road",
            "vehicle_type": "medium_truck"
        }
        
        response = self.client.post(url, bid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['bid_amount']), 25000.00)
        self.assertEqual(self.quote.bids.count(), 1)