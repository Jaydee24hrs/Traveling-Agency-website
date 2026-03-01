from django.test import TestCase

# Create your tests here.
# Transaction/tests.py

import json
import os
from unittest import mock
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import FlutterwaveTransaction
from .forms import FlutterPaymentForm

User = get_user_model()

class FlutterPaymentViewTests(TestCase):
    def setUp(self):
        """
        Set up the test environment.
        """
        # Set the secret key for testing purposes
        self.secret_key = "test_flw_secret_key"
        os.environ['FLW_SECRET_KEY'] = self.secret_key

        # Define the URL for the flutter_payment view
        self.url = reverse('flutter_payment')  # Ensure you have named your URL as 'flutter_payment'

        # Sample valid form data
        self.valid_form_data = {
            'amount': 2500,
            'email': 'testuser@example.com',
            'phone_number': '+2348106756090'
        }

        # Sample invalid form data (missing email)
        self.invalid_form_data = {
            'amount': 2500,
            'email': '',  # Missing email
            'phone_number': '+2348106756090'
        }

        # Sample Flutterwave successful response
        self.flutterwave_success_response = {
            "status": "success",
            "message": "Payment link created",
            "data": {
                "link": "https://checkout.flutterwave.com/pay/test_link"
            }
        }

        # Sample Flutterwave error response
        self.flutterwave_error_response = {
            "status": "error",
            "message": "Invalid API Key"
        }

    @patch('Transaction.views.requests.post')
    def test_flutter_payment_success(self, mock_post):
        """
        Test successful payment initialization.
        """
        # Configure the mock to return a response with status code 200 and a successful JSON payload
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.flutterwave_success_response
        mock_post.return_value = mock_response
        print("mock:",mock_post)

        # Send POST request with valid data
        response = self.client.post(self.url, data=self.valid_form_data)

        # Ensure the Flutterwave API was called with correct parameters
        flutterwave_payload = {
            "tx_ref": mock.ANY,  # tx_ref is dynamically generated
            "amount": self.valid_form_data['amount'],
            "currency": "NGN",
            "redirect_url": mock.ANY,  # redirect_url is dynamically generated
            "customer": {
                "email": self.valid_form_data['email'],
                "phone_number": self.valid_form_data['phone_number']
            },
            "payment_options": "card, banktransfer, ussd",
            "meta": {
                "integration": "django_flutterwave_integration"
            },
          
        }
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.flutterwave.com/v3/payments")
        self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {self.secret_key}")
        self.assertEqual(kwargs['json']['amount'], self.valid_form_data['amount'])
        self.assertEqual(kwargs['json']['customer']['email'], self.valid_form_data['email'])
        self.assertEqual(kwargs['json']['customer']['phone_number'], self.valid_form_data['phone_number'])

        # Check that the response is a redirect to the payment link
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.flutterwave_success_response['data']['link'])

        # Verify that the transaction was created in the database
        transaction = FlutterwaveTransaction.objects.get(tx_ref__startswith='tx-')
        self.assertEqual(transaction.amount, self.valid_form_data['amount'])
        self.assertEqual(transaction.email, self.valid_form_data['email'])
        self.assertEqual(transaction.phone_number, self.valid_form_data['phone_number'])
        self.assertEqual(transaction.status, "Pending")

    def test_flutter_payment_invalid_method(self):
        """
        Test that GET requests are not allowed and return 405 Method Not Allowed.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    
        self.assertJSONEqual(
             str(response.content, encoding='utf8'),
            {"status": "error", "message": "Invalid request method."}
        )

    def test_flutter_payment_invalid_form_data(self):
        """
        Test that invalid form data returns a 400 Bad Request with error messages.
        """
        response = self.client.post(self.url, data=self.invalid_form_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
        self.assertIn('email', response.json()['errors'])

    # @override_settings(FLW_SECRET_KEY=None)
    # @patch('Transaction.views.requests.post')
    # def test_flutter_payment_missing_secret_key(self, mock_post):
    #     """
    #     Test that missing Flutterwave secret key returns a 500 Internal Server Error.
    #     """
    #     # Remove the secret key
    #     del os.environ['FLW_SECRET_KEY']

    #     response = self.client.post(self.url, data=self.valid_form_data)
    #     self.assertEqual(response.status_code, 500)
    #     self.assertJSONEqual(
    #         str(response.content, encoding='utf8'),
    #         {"status": "error", "message": "Payment configuration error."}
    #     )

    #     # Ensure the Flutterwave API was not called
    #     mock_post.assert_not_called()

    # @patch('Transaction.views.requests.post')
    # def test_flutter_payment_api_error_status(self, mock_post):
    #     """
    #     Test that Flutterwave API returning an error status results in a 400 Bad Request.
    #     """
    #     # Configure the mock to return an error response
    #     mock_response = mock.Mock()
    #     mock_response.status_code = 400
    #     mock_response.json.return_value = self.flutterwave_error_response
    #     mock_post.return_value = mock_response

    #     response = self.client.post(self.url, data=self.valid_form_data)

    #     # Ensure the response status code is 400
    #     self.assertEqual(response.status_code, 400)
    #     self.assertJSONEqual(
    #         str(response.content, encoding='utf8'),
    #         {"status": "error", "message": "Invalid API Key"}
    #     )

    #     # Verify that no transaction was created
    #     transactions = FlutterwaveTransaction.objects.all()
    #     self.assertEqual(transactions.count(), 0)

    # @patch('Transaction.views.requests.post')
    # def test_flutter_payment_api_request_timeout(self, mock_post):
    #     """
    #     Test that a timeout during the Flutterwave API request returns a 503 Service Unavailable.
    #     """
    #     # Configure the mock to raise a Timeout exception
    #     mock_post.side_effect = requests.exceptions.Timeout

    #     response = self.client.post(self.url, data=self.valid_form_data)

    #     # Ensure the response status code is 503
    #     self.assertEqual(response.status_code, 503)
    #     self.assertJSONEqual(
    #         str(response.content, encoding='utf8'),
    #         {"status": "error", "message": "Payment service unavailable."}
    #     )

    #     # Verify that the transaction was not created
    #     transactions = FlutterwaveTransaction.objects.all()
    #     self.assertEqual(transactions.count(), 0)

    # @patch('Transaction.views.requests.post')
    # def test_flutter_payment_unexpected_exception(self, mock_post):
    #     """
    #     Test that an unexpected exception during the payment process returns a 500 Internal Server Error.
    #     """
    #     # Configure the mock to raise a generic Exception
    #     mock_post.side_effect = Exception("Unexpected Error")

    #     response = self.client.post(self.url, data=self.valid_form_data)

    #     # Ensure the response status code is 500
    #     self.assertEqual(response.status_code, 500)
    #     self.assertJSONEqual(
    #         str(response.content, encoding='utf8'),
    #         {"status": "error", "message": "An unexpected error occurred."}
    #     )

    #     # Verify that the transaction was not created
    #     transactions = FlutterwaveTransaction.objects.all()
    #     self.assertEqual(transactions.count(), 0)