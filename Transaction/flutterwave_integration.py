import base64
import json
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad
import requests


class FlutterwavePaymentProcessor:
    def __init__(self, encryption_key, secret_key):
        self.encryption_key = encryption_key
        self.secret_key = secret_key
        self.url = "https://api.flutterwave.com/v3/charges?type=card"
        self.validation_url = "https://api.flutterwave.com/v3/validate-charge"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def encrypt_3des(self, payload):
        """Encrypts the payload using 3DES encryption."""
        key = self.encryption_key.ljust(24, '0')[:24]
        cipher = DES3.new(key.encode(), DES3.MODE_ECB)
        padded_data = pad(json.dumps(payload).encode(), DES3.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode()

    def initiate_charge(self, card_details):
        """Initiates the charge request with encrypted card details."""
        encrypted_payload = self.encrypt_3des(card_details)
        response = requests.post(self.url, headers=self.headers, json={"client": encrypted_payload})
        return response.json()

    def process_pin(self, card_details, pin):
        """Processes payment if PIN is required."""
        card_details['authorization'] = {"mode": "pin", "pin": pin}
        encrypted_payload_with_pin = self.encrypt_3des(card_details)
        response = requests.post(self.url, headers=self.headers, json={"client": encrypted_payload_with_pin})
        return response.json()

    def validate_otp(self, otp, flw_ref):
        """Validates OTP if prompted after PIN processing."""
        data = {
            "otp": otp,
            "flw_ref": flw_ref,
            "type": "card"
        }
        response = requests.post(self.validation_url, headers=self.headers, json=data)
        return response.json()


# Replace these with your actual keys


# Initialize the processor with encryption and secret keys
processor = FlutterwavePaymentProcessor(encryption_key, secret_key)

# Card details for the transaction
card_details = {
    "card_number": "5531886652142950",
    "cvv": "564",
    "expiry_month": "09",
    "expiry_year": "32",
    "currency": "NGN",
    "amount": "100",
    "fullname": "Example User",
    "email": "user@example.com",
    "tx_ref": "MC-3243e",
    "redirect_url": "https://www.flutterwave.ng"
}

# Step 1: Initiate the charge
initial_response = processor.initiate_charge(card_details)

# Step 2: Handle PIN and OTP if required
if initial_response['status'] == 'success' and initial_response['meta']['authorization']['mode'] == 'pin':
    pin = input("Enter card PIN: ")
    pin_response = processor.process_pin(card_details, pin)
    print("PIN response:", pin_response)

    if pin_response['status'] == 'success' and 'flw_ref' in pin_response['data']:
        otp = input("Enter OTP: ")
        otp_response = processor.validate_otp(otp, pin_response['data']['flw_ref'])
        print("OTP validation result:", otp_response)
else:
    print("No additional authorization needed or unexpected response:", initial_response)
