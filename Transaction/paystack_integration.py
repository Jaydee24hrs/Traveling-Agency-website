import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class Paystack:
    def __init__(self, ):
        """
        Initialize the Paystack class with your secret key.

        :param secret_key: Paystack secret key for authentication.
        """
        self.secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        self.base_url = "https://api.paystack.co/transaction/initialize"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    def verify_payment(self, ref:str)-> dict[str, Any]:
        """
        Verifies the transaction using paystack API
        
        :param ref: The transaction reference to verify.
        :return: The status of the transaction or error message
        """
        verify_url: str = f"{self.base_url}/verify/{ref}"
        
        try:
            response: requests.Response = requests.get(verify_url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            return{"status": False, "message": str(e)}
        except requests.HTTPError as http_err:
            return {"status": False, "message": "HTTP error occurred", "details": str(http_err)}
        except requests.ConnectionError:
            return {"status": False, "message": "Connection error occurred"}
        except requests.Timeout:
            return {"status": False, "message": "Request timed out"}
        
        
        
        # if response.status_code == 200:
        #     print(response.json())
        #     return response.json()
        # else:
        #     return {"status": False, "message": response.json().get("message")}
            
    def create_payment_link(self, name, email, description, amount, redirect_url, custom_fields=None, currency="NGN"):
        """
        Create a payment link using Paystack API.

        :param name: Name of the payment link.
        :param description: Description of the payment.
        :param amount: Amount in kobo (100 kobo = 1 Naira).
        :param redirect_url: The URL to redirect after payment completion.
        :param custom_fields: Optional custom fields (list of dictionaries).
        :param currency: Currency for the transaction (default is "NGN").
        :return: Payment link URL or error message.
        """
        url = f"{self.base_url}/"
        data = {
            "name": name,
            "description": description,
            "amount": amount,
            "email": email,
            "currency": currency,
            "callback_url": redirect_url
        }

        # Add custom fields if provided
        if custom_fields:
            data["custom_fields"] = custom_fields

        # Send the POST request to Paystack API
        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.json().get('message')}"

    
    def verify_payment(self, reference):
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        response = requests.get(url, headers=self.headers)
        # Check if the request was successful and print the response
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print("Verification failed:", response.status_code, response.text)

    