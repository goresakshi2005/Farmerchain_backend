from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from farmer.models import Farmer, FarmerQuoteRequest
from .models import FPO

class FPOBidWorkflowTests(APITestCase):
    """
    Tests for the FPO workflow: viewing quotes and submitting bids.
    """
    def setUp(self):
        """
        Set up a Farmer with a quote, and an FPO to bid on it.
        """
        # Create a Farmer and a quote
        self.farmer = Farmer.objects.create(
            name="Jane Farmer", email="jane@farm.com", aadhaar_number="987654321098",
            wallet_address="0xFarmerJaneWallet", city="Greenfield", state="Pastures",
            approval_status='approved'
        )
        self.farmer.set_password("farmerpass")
        self.farmer.save()
        
        self.quote = FarmerQuoteRequest.objects.create(
            farmer=self.farmer, product_name="Corn", category="Grains",
            deadline="2025-10-10", quantity=2000, unit="kg", description="Non-GMO corn"
        )

        # Create an FPO
        self.fpo = FPO.objects.create(
            name="Agri Corp", email="agri@corp.com", corporate_identification_number="CIN987654321",
            wallet_address="0xFPOAgriCorpWallet", city="Metro", state="Commerce",
            approval_status='approved'
        )
        self.fpo.set_password("fpopass")
        self.fpo.save()

        # Get FPO's token
        self.fpo_token = self.get_token('agri@corp.com', 'fpopass', 'fpo')

    def get_token(self, username, password, role):
        """Helper function to get JWT token."""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': username, 'password': password, 'role': role}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_fpo_can_view_open_farmer_quotes(self):
        """
        Ensure an authenticated FPO can see a list of open quotes from farmers.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        url = reverse('open-farmer-quote-list')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect to see the one quote we created in setUp
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.quote.id)
        self.assertEqual(response.data[0]['product_name'], "Corn")

    def test_fpo_can_submit_bid(self):
        """
        Ensure an authenticated FPO can submit a valid bid to an open quote.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        
        # The URL for submitting a bid is a custom action on the quote detail view
        url = reverse('open-farmer-quote-submit-bid', kwargs={'pk': self.quote.id})
        
        bid_data = {
            "bid_amount": 15000.50,
            "delivery_time": 7,
            "comments": "We can handle this delivery efficiently.",
            "transport_mode": "road",
            "vehicle_type": "large_truck"
        }
        
        response = self.client.post(url, bid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['bid_amount']), 15000.50)
        self.assertEqual(self.quote.bids.count(), 1)