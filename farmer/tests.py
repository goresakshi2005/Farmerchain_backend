from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Farmer
from fpo.models import FPO, FPOBid

class FarmerQuoteWorkflowTests(APITestCase):
    """
    Tests for the entire Farmer workflow: creating quotes and managing bids.
    """
    def setUp(self):
        """
        Set up initial data for tests: create a Farmer and an FPO user.
        """
        # Create a Farmer
        self.farmer = Farmer.objects.create(
            name="Test Farmer",
            email="farmer@test.com",
            aadhaar_number="123456789012",
            wallet_address="0xFarmerWalletAddress",
            city="Farmville",
            state="Agriculture",
            approval_status='approved'
        )
        self.farmer.set_password("farmerpassword")
        self.farmer.save()

        # Create an FPO
        self.fpo = FPO.objects.create(
            name="Test FPO",
            email="fpo@test.com",
            corporate_identification_number="CIN123456789",
            wallet_address="0xFPOWalletAddress",
            city="Marketon",
            state="Commerce",
            approval_status='approved'
        )
        self.fpo.set_password("fpopassword")
        self.fpo.save()

        # Get JWT tokens for authentication
        self.farmer_token = self.get_token('farmer@test.com', 'farmerpassword', 'farmer')
        self.fpo_token = self.get_token('fpo@test.com', 'fpopassword', 'fpo')

    def get_token(self, username, password, role):
        """Helper function to get JWT token."""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': username, 'password': password, 'role': role}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_farmer_can_create_quote(self):
        """
        Ensure an authenticated farmer can create a new quote request.
        """
        # Authenticate as the farmer
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        
        url = reverse('farmer-quote-list')
        data = {
            "product_name": "Organic Wheat",
            "category": "Grains",
            "description": "High quality organic wheat.",
            "deadline": "2025-12-31",
            "quantity": 1000,
            "unit": "kg"
        }
        response = self.client.post(url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product_name'], "Organic Wheat")
        self.assertEqual(response.data['farmer_name'], self.farmer.name)

    def test_farmer_can_view_and_accept_bid(self):
        """
        Ensure a farmer can view bids on their quote and accept one.
        """
        # 1. Farmer creates a quote
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        quote_url = reverse('farmer-quote-list')
        quote_data = {
            "product_name": "Tomatoes", "category": "Vegetables", "deadline": "2025-11-30",
            "quantity": 500, "unit": "kg", "description": "Fresh tomatoes"
        }
        quote_response = self.client.post(quote_url, quote_data, format='json')
        self.assertEqual(quote_response.status_code, status.HTTP_201_CREATED)
        quote_id = quote_response.data['id']

        # 2. FPO submits a bid
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        bid_url = reverse('open-farmer-quote-submit-bid', kwargs={'pk': quote_id})
        bid_data = {"bid_amount": 7500.00, "delivery_time": 5, "transport_mode": "road", "vehicle_type": "medium_truck"}
        bid_response = self.client.post(bid_url, bid_data, format='json')
        self.assertEqual(bid_response.status_code, status.HTTP_201_CREATED)
        bid_id = bid_response.data['id']

        # 3. Farmer views the bids on the quote
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        view_bids_url = reverse('farmer-quote-bids', kwargs={'pk': quote_id})
        bids_response = self.client.get(view_bids_url, format='json')
        self.assertEqual(bids_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(bids_response.data), 1)
        self.assertEqual(bids_response.data[0]['id'], bid_id)

        # 4. Farmer accepts the bid
        accept_url = reverse('farmer-quote-accept-bid', kwargs={'pk': quote_id})
        accept_response = self.client.post(accept_url, {'bid_id': bid_id}, format='json')
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertEqual(accept_response.data['status'], f'Bid {bid_id} accepted.')

        # 5. Verify database state
        accepted_bid = FPOBid.objects.get(id=bid_id)
        quote = accepted_bid.quote
        self.assertEqual(accepted_bid.status, 'accepted')
        self.assertEqual(quote.status, 'awarded')
        self.assertEqual(quote.accepted_bid, accepted_bid)