from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from farmer.models import Farmer, FarmerQuoteRequest
from fpo.models import FPO, FPOBid
from .models import Negotiation

class NegotiationWorkflowTests(APITestCase):
    def setUp(self):
        self.farmer = Farmer.objects.create(
            name="Negotiation Farmer", email="negfarmer@test.com", aadhaar_number="111222333444",
            wallet_address="0xNegFarmer", city="Farmville", state="Agri", approval_status='approved'
        )
        self.farmer.set_password("farmerpass")
        self.farmer.save()

        self.fpo = FPO.objects.create(
            name="Negotiation FPO", email="negfpo@test.com", corporate_identification_number="CINNEG123",
            wallet_address="0xNegFPO", city="Marketon", state="Commerce", approval_status='approved'
        )
        self.fpo.set_password("fpopass")
        self.fpo.save()

        self.farmer_token = self.get_token('negfarmer@test.com', 'farmerpass', 'farmer')
        self.fpo_token = self.get_token('negfpo@test.com', 'fpopass', 'fpo')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        
        # --- FIX IS HERE: Added the required 'description' field ---
        quote_data = {
            "product_name": "Soybeans", 
            "category": "Legumes", 
            "description": "Premium quality soybeans for processing.", # <-- ADDED THIS
            "deadline": "2025-12-01", 
            "quantity": 3000, 
            "unit": "kg"
        }
        quote_response = self.client.post(reverse('farmer-quote-list'), quote_data, format='json')
        self.assertEqual(quote_response.status_code, status.HTTP_201_CREATED)
        self.quote_id = quote_response.data['id']
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        
        # Also adding optional 'comments' to bid data for completeness
        bid_data = {
            "bid_amount": 20000.00, 
            "delivery_time": 10,
            "comments": "Willing to negotiate on price for a long term contract."
        }
        bid_response = self.client.post(
            reverse('open-farmer-quote-submit-bid', kwargs={'pk': self.quote_id}), 
            bid_data, 
            format='json'
        )
        self.assertEqual(bid_response.status_code, status.HTTP_201_CREATED)
        self.bid_id = bid_response.data['id']

        self.bid_instance = FPOBid.objects.get(id=self.bid_id)
        self.negotiation = Negotiation.objects.create(bid=self.bid_instance)

    def get_token(self, username, password, role):
        response = self.client.post(reverse('token_obtain_pair'), {'username': username, 'password': password, 'role': role}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_participants_can_view_negotiation(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        url = reverse('negotiation-detail', kwargs={'pk': self.negotiation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.negotiation.id)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_full_negotiation_flow_accept(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        msg_url = reverse('negotiation-send-message', kwargs={'pk': self.negotiation.id})
        msg_data = {"message": "We can do it for 19500.", "counter_amount": 19500.00}
        response = self.client.post(msg_url, msg_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        accept_url = reverse('negotiation-accept', kwargs={'pk': self.negotiation.id})
        response = self.client.post(accept_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.negotiation.refresh_from_db()
        self.bid_instance.refresh_from_db()
        quote = FarmerQuoteRequest.objects.get(id=self.quote_id)
        
        self.assertEqual(self.negotiation.status, 'accepted')
        self.assertEqual(self.bid_instance.status, 'accepted')
        self.assertEqual(quote.status, 'awarded')

    def test_full_negotiation_flow_reject(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.fpo_token)
        msg_url = reverse('negotiation-send-message', kwargs={'pk': self.negotiation.id})
        self.client.post(msg_url, {"message": "Final offer."}, format='json')
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.farmer_token)
        reject_url = reverse('negotiation-reject', kwargs={'pk': self.negotiation.id})
        response = self.client.post(reject_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.negotiation.refresh_from_db()
        self.bid_instance.refresh_from_db()
        self.assertEqual(self.negotiation.status, 'rejected')
        self.assertEqual(self.bid_instance.status, 'rejected')