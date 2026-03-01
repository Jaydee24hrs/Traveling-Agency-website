import json
import logging
import os
import asyncio
import aiohttp

import requests
from dotenv import load_dotenv

from Markup.models import ExchangeRate, ExchangeRateExclution, TykttMarkUp

load_dotenv()

default_office_ids = {
    "LOSN828HJ": "NGN",
}


# def get_flights_ids():
#     office_ids = {
#         "LOSN828HJ": "NGN",
#     }
#     return office_ids

def get_flights_ids():
    office_ids = {
        
    }
    all_active_office_id = ExchangeRate.objects.filter(status=True)
    if all_active_office_id:
        office_ids = {}
        for office_id in all_active_office_id:
            office_ids[office_id.office_id] = office_id.currency
    return office_ids


# def get_corporate_codes():
#     corporate_codes = [item for item in TykttMarkUp.objects.filter()
#                         .exclude(corporate_code__isnull=True)
#                         .values_list('corporate_code', flat=True) if item]
#     corporate_codes = [text.split('/')[1] for text in corporate_codes]
#     return corporate_codes

def get_corporate_codes():
    raw_codes = TykttMarkUp.objects.exclude(corporate_code__isnull=True).values_list('corporate_code', flat=True)
    corporate_codes = []

    for entry in raw_codes:
        if not entry:
            continue
        # Split by comma in case there are multiple codes in one string
        parts = entry.split(',')
        for part in parts:
            if '/' in part:
                last_segment = part.strip().split('/')[-1]
                if last_segment.isdigit():
                    corporate_codes.append(last_segment)

    return corporate_codes

def get_include_and_exclude_carrier_code():
    include_airline = ExchangeRate.objects.all()
    exclude_airline = ExchangeRateExclution.objects.all()  # Corrected typo in model name
    data = {}
    # Process include_airline entries
    for rate in include_airline:
        office_id = rate.office_id
        currency = rate.currency
        if office_id not in data:
            data[office_id] = {}
        if currency not in data[office_id]:
            # Initialize both lists for new currency entries
            data[office_id][currency] = {'include_airlines': "", 'exclude_airlines': ""}
        if rate.marketing_carrier:  # Only append if not None
            data[office_id][currency]['include_airlines'] = rate.marketing_carrier
    # Process exclude_airline entries
    for rate in exclude_airline:
        office_id = rate.office_id
        currency = rate.currency
        if office_id not in data:
            data[office_id] = {}
        if currency not in data[office_id]:
            # Initialize both lists for new currency entries
            data[office_id][currency] = {'include_airlines': "", 'exclude_airlines': ""}
        if rate.marketing_carrier:  # Only append if not None
            data[office_id][currency]['exclude_airlines'] = rate.marketing_carrier
    return data




class AmadeusAPI:
    def __init__(self, guest_office_ids=None):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.guest_office_ids = guest_office_ids if guest_office_ids else get_flights_ids()
        self.token_type = None
        self.access_token = None
        self.expires_in = None
        self.state = None
        self.scope = None
        self.type = None
        self.username = None
        self.application_name = None
        self.tokens = {}
        self.url = os.getenv('AMADEUS_URL')
        self.get_oauth_tokens()
        self.corporate_code = get_corporate_codes()
        self.include_and_exclude_carrier_code = get_include_and_exclude_carrier_code()

    def get_oauth_tokens(self):
        if type(self.guest_office_ids) == str:
            self.guest_office_ids = {self.guest_office_ids: default_office_ids[self.guest_office_ids]}
        for guest_office_id, currency in self.guest_office_ids.items():
            url = f"{self.url}/v1/security/oauth2/token"
            payload = f'client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials&guest_office_id={guest_office_id}'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.tokens[guest_office_id] = {
                    "type": response_data.get("type"),
                    "username": response_data.get("username"),
                    "application_name": response_data.get("application_name"),
                    "token_type": response_data.get("token_type"),
                    "access_token": response_data.get("access_token"),
                    "expires_in": response_data.get("expires_in"),
                    "state": response_data.get("state"),
                    "scope": response_data.get("scope"),
                    "guest_office_id": response_data.get("guest_office_id"),
                    "currency": currency
                }
            else:
                logging.error(
                    f"Failed to retrieve token for guest office ID {guest_office_id}: {response.status_code} {response.text}")

    def search_flight(self, travelers=None, originDestinations=None, travelClass=None,
                      currency="USD", phone_search=False):
        results = {}

        # If phone_search is True, limit to the two specific guest office IDs
        if phone_search:
            guest_office_ids_to_use = ['LOSN828HJ']
        else:
            guest_office_ids_to_use = self.tokens.keys()  # Use all available guest office IDs

        for guest_office_id in guest_office_ids_to_use:
            # Ensure the guest office ID exists in self.tokens
            if guest_office_id not in self.tokens:
                continue

            token_data = self.tokens[guest_office_id]

            try:
                # fare_types = ['PUBLISHED']
                # if guest_office_id in ["LOSN828HJ"]:
                # fare_types.append("NEGOTIATED")

                url = f"{self.url}/v2/shopping/flight-offers"
                payload = json.dumps({
                    "currencyCode": currency,
                    "originDestinations": originDestinations,
                    "travelers": travelers,
                    "sources": ["GDS"],
                    "searchCriteria": {
                        "flightFilters": {
                            "cabinRestrictions": [
                                {
                                    "cabin": travelClass,
                                    "coverage": "ALL_SEGMENTS",
                                    "originDestinationIds": [str(i['id']) for i in originDestinations]
                                }
                            ]
                        },
                        "additionalInformation": {
                            "chargeableCheckedBags": False,
                            "brandedFares": True,
                            "fareRules": True,
                        },
                        "pricingOptions": {
                            "fareType": ['PUBLISHED', 'NEGOTIATED'],
                            "includedCheckedBagsOnly": False,
                        }
                    }
                })
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token_data["access_token"]}',
                    'ama-client-ref': 'travelyakata002'
                }

                logging.info(f"Requesting flights for guest office ID {guest_office_id} with payload: {payload}")
                response = requests.post(url, headers=headers, data=payload)
                if not response.ok:
                    logging.error(f"Failed to search flight for guest office ID {guest_office_id}: {response.status_code} {response.text}")
                response.raise_for_status()  # Raise error for non-success status codes

                result_data = response.json()

                # Limit the number of flight offers to 10
                if "data" in result_data:
                    result_data["data"] = result_data["data"]
                    # Add fare basis if available
                    for offer in result_data["data"]:
                        fare_basics = offer.get("fareBasis")
                        if fare_basics:
                            offer["fareBasics"] = fare_basics

                results[guest_office_id] = result_data

            except requests.RequestException as e:
                error_content = e.response.text if e.response else str(e)
                logging.error(
                    f"Failed to search flight for guest office ID {guest_office_id}: {e}\nError content: {error_content}")
                results[guest_office_id] = {"error": error_content}

        return results

    def get_fare_rule(self, flight_data=None):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/shopping/flight-offers/pricing?include=detailed-fare-rules"
            payload = json.dumps({
                "data": {
                    "type": "flight-offers-pricing",
                    "flightOffers": [
                        flight_data
                    ]
                }
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            response = requests.post(url, headers=headers, data=payload)
            if not response.ok:  # or explicitly: if response.status_code not in range(200, 300)
                    logging.error(f"Failed to Get Fare rule: {response.status_code} {response.text}")

            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")
    
    async def _fetch_flight(self, session, guest_office_id, travelers, originDestinations, travelClass, currency, cabinRestrictions):
        """Async helper method to fetch flight data for a single guest office ID."""
        token_data = self.tokens.get(guest_office_id)
        if not token_data:
            logging.error(f"No token found for guest office ID {guest_office_id}")
            return guest_office_id, {"error": "No token found"}
        
        carrier_restrictions = {}
        fare_types = ["PUBLISHED", "NEGOTIATED"]
        if self.corporate_code:
            fare_types.append("CORPORATE")
        if currency == "NGN" and guest_office_id == "ACCG828TY":
            currency = "GHS"
        included_carriers = self.include_and_exclude_carrier_code.get(guest_office_id, {}).get(currency, {}).get('include_airlines', [])
        excluded_carriers = self.include_and_exclude_carrier_code.get(guest_office_id, {}).get(currency, {}).get('exclude_airlines', [])

        if included_carriers:
            carrier_restrictions["includedCarrierCodes"] = included_carriers.split(",")

        if excluded_carriers:
            carrier_restrictions["excludedCarrierCodes"] = excluded_carriers.split(",")

        url = f"{self.url}/v2/shopping/flight-offers"
        payload = json.dumps({
            "currencyCode": currency,
            "originDestinations": originDestinations,
            "travelers": travelers,
            "sources": ["GDS"],
            "searchCriteria": {
                "flightFilters": {
                    "cabinRestrictions": cabinRestrictions,
                    "carrierRestrictions": carrier_restrictions if carrier_restrictions else None
                },
                "additionalInformation": {
                    "chargeableCheckedBags": False,
                    "brandedFares": True,
                    "fareRules": True,
                },
                "pricingOptions": {
                    "fareType": fare_types,
                    "includedCheckedBagsOnly": False,
                    "corporateCodes": self.corporate_code
                }
            }
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token_data["access_token"]}',
            'ama-client-ref': 'travelyakata002'
        }

        async with session.post(url, headers=headers, data=payload) as response:
            if response.status != 200:
                error_content = await response.text()
                logging.error(f"Failed to search flight for guest office ID {guest_office_id}: {error_content}")
                return guest_office_id, {"error": error_content}
            return guest_office_id, await response.json()

    async def search_flight_v2(self, travelers=None, originDestinations=None, travelClass=None, phone_search=False, currency="USD", cabinRestrictions=None):
        results = {}
        guest_office_ids_to_use = ['LOSN828HJ'] if phone_search else list(
            self.tokens.keys())

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_flight(session, guest_office_id, travelers, originDestinations, travelClass, currency, cabinRestrictions)
                for guest_office_id in guest_office_ids_to_use if guest_office_id in self.tokens
            ]
            results_list = await asyncio.gather(*tasks)

            # Aggregate results by guest office ID
            results = {guest_office_id: data for guest_office_id, data in results_list}

        return results
            

    def flight_pricing(self, flight_data):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/shopping/flight-offers/pricing"
            payload = json.dumps({
                "data": {
                    "type": "flight-offers-pricing",
                    "flightOffers": [
                        flight_data
                    ]
                }
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            response = requests.post(url, headers=headers, data=payload)
            if not response.ok:  # or explicitly: if response.status_code not in range(200, 300)
                logging.error(
                    f"Request failed with status For flight Booking {response.status_code}. Issuance Response: {response.text}"
                )
            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def book_flight(self, travelers, flight_data, flight_id, contacts):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/booking/flight-orders"
            payload = json.dumps({
                "data": {
                    "type": "flight-order",
                    "flightOffers": [flight_data],
                    "travelers": travelers,
                    # "contacts": [contacts],
                    "ticketingAgreement": {
                        "option": "DELAY_TO_CANCEL",
                        "delay": "3D"},
                    "formOfPayments": [
                        {
                            "other": {
                                "method": "CASH",
                                "flightOfferIds": [
                                    flight_id
                                ]
                            }
                        }
                    ]
                }
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            response = requests.post(url, headers=headers, data=payload)
            if not response.ok:  # or explicitly: if response.status_code not in range(200, 300)
                logging.error(
                    f"Request failed with status For flight Booking {response.status_code}. Issuance Response: {response.text}"
                )
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def cancel_flight(self, flight_id):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/booking/flight-orders/{flight_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = ""
            response = requests.request("DELETE", url, headers=headers, data=payload)
            return response
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def update_flight_traveller_document(self, flight_id, travelers):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/booking/flight-orders/{flight_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = json.dumps({
                "data": {
                    "type": "flight-order",
                    "id": flight_id,
                    "travelers": travelers
                }
            })
            response = requests.request("PATCH", url, headers=headers, data=payload)
            response.raise_for_status()
            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def get_flight_data(self, flight_id):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/booking/flight-orders/{flight_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = ""
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def get_flight_data_by_pnr(self, pnr, systemcode):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/booking/flight-orders/by-reference?reference={pnr}&originSystemCode={systemcode}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = ""
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def get_seat_map(self, flight_id):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/shopping/seatmaps?flightOrderId={flight_id}&seatNumberServiceBookingStatusRequired=true&flight-orderId={flight_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = ""
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")

    def get_flight_availability(self, travelers, source, originDestinations, includedCarrierCodes):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/shopping/availability/flight-availabilities"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = json.dumps(
                {
                    "originDestinations": originDestinations,
                    "travelers": travelers,
                    "sources": [
                        source
                    ],
                    "searchCriteria": {
                        "excludeAllotments": False,
                        "flightFilters": {
                            "connectionRestriction": {
                                "maxNumberOfConnections": 2
                            },
                            "carrierRestrictions": {
                                "blacklistedInEUAllowed": True,
                                "includedCarrierCodes": [
                                    includedCarrierCodes
                                ]
                            }
                        },
                        "includeClosedContent": False
                    }
                }
            )
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")
            

    def get_upsell(self, flight_data):
        try:
            token_data = self.tokens.items()
            items_list = list(token_data)
            token = items_list[0][1]['access_token']
            url = f"{self.url}/v1/shopping/flight-offers/upselling"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'ama-client-ref': 'travelyakata002'
            }
            payload = json.dumps(
                {
                    "data": {
                        "type": "flight-offers-upselling",
                        "flightOffers": [
                            flight_data
                        ]
                    }
                }
            )
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            result_data = response.json()
            return result_data
        except requests.RequestException as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")
