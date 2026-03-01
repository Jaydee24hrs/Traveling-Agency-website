import requests

class Paystack:
    def __init__(self, secret_key):
        """
        Initialize the Paystack class with your secret key.

        :param secret_key: Paystack secret key for authentication.
        """
        self.secret_key = secret_key
        self.base_url = "https://api.paystack.co/transaction/initialize"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

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
            "currency": "USD",
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


# Example usage
if __name__ == "__main__":
    # Replace with your actual secret key
    secret_key = 'sk_test_9e70cd8fc8ce7c586ccbaff0d58e9a290e3ffd63'

    # Create an instance of the Paystack class
    paystack = Paystack(secret_key)
    print(paystack)

    # Generate a payment link
    payment_link = paystack.create_payment_link(
        name="Payment for Services",
        email="customer@example.com",
        description="Payment for XYZ services",
        amount=500000,  # 5000 Naira (500,000 kobo)
        redirect_url="http://127.0.0.1:8000/transaction/verify-payment/",
        custom_fields=[{"display_name": "Customer ID", "variable_name": "customer_id", "value": "12345", "pnr": "FHYHIK"}]
    )

    # Print the generated payment link or error
    print(payment_link)


# curl https://api.paystack.co/transaction/verify/53etvic11r
# -H "Authorization: Bearer sk_test_DEFAULT"
# -X GET
