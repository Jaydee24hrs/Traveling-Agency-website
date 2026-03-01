from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
import re

from Markup.models import ExchangeRate, MarkupRuleTyktt, TykttMarkUp

def calculate_markup_fee_new(flight_data, office_id):
    total_price = 0
    carrier_code = flight_data["itineraries"][0]["segments"][0]["carrierCode"]
    # Preload markup rules and commissions
    tyktt_markup_rules = TykttMarkUp.objects.prefetch_related('tyktt_commission').filter(
        marketing_carrier__icontains=carrier_code) or TykttMarkUp.objects.prefetch_related('tyktt_commission').filter(is_others=True)

    validation_carrier = flight_data.get('validatingAirlineCodes', [None])[0]
    segments = flight_data["itineraries"][0]["segments"]
    # operating_airline = next((seg["operating"]['carrierCode'] for seg in segments if seg.get('operating')), '')
    operating_airline = next(
        (
            seg["operating"]["carrierCode"]
            for seg in segments
            if seg.get("operating") and seg["operating"]["carrierCode"] != carrier_code
        ),
        carrier_code  # Default to carrier_code if no different operating carrier is found
    )

    currency = flight_data.get('price', {}).get('currency') or flight_data.get('price', {}).get('billingCurrency')
    fare_type = flight_data["pricingOptions"]["fareType"][0].lower()
    from_city = segments[0]["departure"]["iataCode"]
    to_city = segments[0]["arrival"]["iataCode"]

    # Batch query for country data
    city_data = City.objects.filter(airport_code__in=[from_city, to_city]).values('airport_code', 'country_code')
    city_map = {city['airport_code']: city['country_code'] for city in city_data}
    from_country = city_map.get(from_city, '')
    to_country = city_map.get(to_city, '')

    # Pre-compute office ID list for faster access
    for markup in tyktt_markup_rules:
        # Iterate through related commissions
        for commission in markup.tyktt_commission.all():
            cleaned_office_ids = [office_id.strip() for office_id in commission.office_id.split(',')]
            if (commission.office_id is None or office_id in cleaned_office_ids) and (commission.currency == currency or commission.currency.lower() == 'all' or commission.currency is None or commission.currency == '') and (commission.fare_type is None or commission.fare_type.lower() == 'all' or commission.fare_type.lower() == fare_type):
                if commission.validating_carrier is None or commission.validating_carrier == validation_carrier or commission.validating_carrier == '':
                    # Simplify departure and arrival checks
                    departure_match = (
                            commission.departure is None or commission.departure == "" or
                            (
                                    commission.departure_type == "Country" and
                                    (from_country in [item for item in commission.departure.split(",") if not item.startswith("!")] or
                                    f"!{from_country}" not in [item for item in commission.departure.split(",") if item.startswith("!")] and
                                    [item for item in commission.departure.split(",") if not item.startswith("!")] in ([], ['']))
                            ) or
                            (
                                    commission.departure_type == "City" and
                                    (from_city in [item for item in commission.departure.split(",") if not item.startswith("!")] or
                                    f"!{from_city}" not in [item for item in commission.departure.split(",") if item.startswith("!")] and
                                    [item for item in commission.departure.split(",") if not item.startswith("!")] in ([], ['']))
                            )
                    )

                    arrival_match = (
                            commission.arrival is None or commission.arrival == "" or
                            (
                                    commission.arrival_type == "Country" and
                                    (to_country in [item for item in commission.arrival.split(",") if not item.startswith("!")] or
                                    f"!{to_country}" not in [item for item in commission.arrival.split(",") if item.startswith("!")] and
                                    [item for item in commission.arrival.split(",") if not item.startswith("!")] in ([], ['']))
                            ) or
                            (
                                    commission.arrival_type == "City" and
                                    (to_city in [item for item in commission.arrival.split(",") if not item.startswith("!")] or
                                    f"!{to_city}" not in [item for item in commission.arrival.split(",") if item.startswith("!")] and
                                    [item for item in commission.arrival.split(",") if not item.startswith("!")] in ([], ['']))
                            )
                    )
                    if not (departure_match and arrival_match):
                        continue
                    if commission.operating_carrier is None or commission.operating_carrier == '' or \
                            (operating_airline in [item for item in commission.operating_carrier.split(",") if not item.startswith("!")] or [item for item in commission.operating_carrier.split(",") if not item.startswith("!")] == [] ) and \
                            f"!{operating_airline}" not in [item for item in commission.operating_carrier.split(",") if item.startswith("!")]:

                        for traveller in flight_data['travelerPricings']:
                            if traveller['fareDetailsBySegment'][0]['cabin'].lower() != commission.carbin_class.lower() and commission.carbin_class != "ALL":
                                continue
                            if str(traveller.get("travelerType", "")).replace('HELD_',
                                                                              '').lower() != commission.passenger.lower() and commission.passenger != "ALL":
                                continue
                            base_price = float(traveller['price']['base'])
                            markup_amount = 0
                            if commission.markup_commission == "Commission":
                                if commission.amount_type == "Percentage" or commission.amount_type == "%":
                                    markup_amount = (float(commission.amount) / 100) * base_price
                                    ten_percent = markup_amount * 0.10
                                    markup_amount = markup_amount - ten_percent
                                elif commission.amount_type == "Fixed":
                                    markup_amount = float(commission.amount)
                                total_price -= markup_amount

                            elif commission.markup_commission == "Markup":
                                if commission.amount_type == "Percentage":
                                    markup_amount = (float(commission.amount) / 100) * base_price
                                elif commission.amount_type == "Fixed":
                                    markup_amount = float(commission.amount)
                                total_price += markup_amount
    return total_price



def replace_hyphens_with_underscores(data):
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = key.replace('-', '_')
            new_data[new_key] = replace_hyphens_with_underscores(value)
        return new_data
    elif isinstance(data, list):
        return [replace_hyphens_with_underscores(item) for item in data]
    else:
        return data


def convert_currency():
    default_dict = {
        "LOSN828HJ": 1.00,
    }
    return default_dict


def converter_data(office_id):
    exchange_rate = ExchangeRate.objects.filter(office_id=office_id).first()
    if exchange_rate:
        return exchange_rate.rate
    return 1.0


def get_currency_exchnage_rate(currency):
    exchange_rate = ExchangeRate.objects.filter(currency=currency).first()
    if exchange_rate:
        return exchange_rate.rate
    return 1.0

# Booking Information Model
class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('Reserved', 'Reserved'),
        ('Cancelled', 'Cancelled'),
        # ('Ticketed', 'Ticketed'),
        ('Voided', 'Voided'),
        ('Issued', 'Issued'),
        ('Refunded', 'Refunded'),
        ('Exchanged', 'Exchanged'),
    ]
    BOOKING_PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Successful", "Successful"),
        ("Failed", "Successful"),
        ("In progress", "In progress")
    ]

    booking_date = models.DateField(auto_now_add=True)
    pnr = models.CharField(max_length=20)
    booking_id = models.CharField(max_length=250, unique=True, null=True, blank=True)
    office_id = models.CharField(max_length=20, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    expiry_date_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default="Reserved")
    user = models.ForeignKey("User.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    user_name = models.CharField(max_length=255, blank=True, null=True)
    user_email = models.EmailField(blank=True, null=True)
    user_access_type = models.CharField(max_length=255, blank=True, null=True)
    user_phone = models.CharField(max_length=255, blank=True, null=True)
    response = models.JSONField(blank=True, null=True)
    init_response = models.JSONField(blank=True, null=True)
    flight_data = models.JSONField(blank=True, null=True)
    new_flight_price = models.JSONField(blank=True, null=True)
    airlines = models.JSONField(blank=True, null=True)
    base_fare = models.JSONField(blank=True, null=True)
    tax_fee = models.JSONField(blank=True, null=True)
    total = models.JSONField(blank=True, null=True)
    farerules = models.JSONField(blank=True, null=True)
    seatmap = models.JSONField(blank=True, null=True)
    agency_currency_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    mark_up = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    tyktt_currency_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=50, blank=True, null=True)
    issued_total_taxes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    issued_converted_base_fare = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    issued_converted_total_fare = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    booking_payment = models.CharField(max_length=20, default="Pending", choices=BOOKING_PAYMENT_STATUS)
    payment_type = models.CharField(max_length=100, default="Bank Transfer/Cash")

    def __str__(self):
        return f"{self.pnr}"

    def save(self, *args, **kwargs):
        markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        self.new_flight_price = ""
        if self.farerules:
            self.farerules = replace_hyphens_with_underscores(self.farerules)
        if self.status == 'Reserved':
            if self.response:

                to_multiply = 1
                if self.flight_data.get('is_converted', False):
                    to_multiply = get_currency_exchnage_rate(self.currency)

                input_string = self.response['data']['remarks'].get('airline')
                price = self.response['data']['flightOffers'][0].get('price')
                if price:
                    self.currency = price['currency']
                    amount_to_add = 0.00

                    self.agency_currency_price = (float(price['grandTotal']) + amount_to_add ) * float(to_multiply)
                    # self.tyktt_currency_price = float(price['grandTotal']) * float(float(to_multiply))

                    self.tyktt_currency_price =  float(float(price['grandTotal']) + amount_to_add) * float(to_multiply)

                    amount_to_add += calculate_markup_fee_new(self.response['data']['flightOffers'][0], self.office_id)
                    self.tyktt_currency_price =  float(float(price['grandTotal']) + amount_to_add)

            if self.new_flight_price:
                price = self.new_flight_price['price'].get('grandTotal')
                self.currency = self.new_flight_price['price']['billingCurrency']
                self.agency_currency_price =  float(price)
                self.tyktt_currency_price =  float(price)

                amount_to_add = 0.00
                amount_to_add = calculate_markup_fee_new(self.new_flight_price, self.office_id)
                self.tyktt_currency_price =  float(float(price) + amount_to_add)

            if input_string:
                for key in input_string:
                    if key['subType'] == "ADVANCED_TICKET_TIME_LIMIT":
                        text = key.get('text', '')
                        if text:
                            self.ticking_time_limit = text
                            
        if self.user:
            self.user_name = f"{self.user.first_name} {self.user.last_name}"
            self.user_email = self.user.email
            self.user_access_type = self.user.access_type
            self.user_phone = self.user.phone

        super().save(*args, **kwargs)

    @property
    def formatted_id(self):
        return f"JT-{10000000 + self.id}"


# Passenger Information Model
class Passenger(models.Model):
    PASSENGER_TYPE_CHOICES = [
        ('Adult', 'Adult'),
        ('Child', 'Child'),
        ('Infant', 'Infant'),
    ]

    full_name = models.CharField(max_length=255)
    passenger_type = models.CharField(max_length=20, choices=PASSENGER_TYPE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    ticket_number = models.CharField(max_length=20)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')

    def __str__(self):
        return self.full_name


# Itinerary Information Model
class Itinerary(models.Model):
    date = models.DateField()
    pnr = models.CharField(max_length=20)
    airline_ref = models.CharField(max_length=50)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='itinerary')

    def __str__(self):
        return f"Itinerary for PNR: {self.pnr}"


class City(models.Model):
    country_code = models.CharField(max_length=10, blank=True, null=True)
    city_code = models.CharField(max_length=10, blank=True, null=True)
    city_name = models.CharField(max_length=100, blank=True, null=True)
    provider = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    airport = models.CharField(max_length=100, blank=True, null=True)
    airport_code = models.CharField(max_length=100, blank=True, null=True)
    state_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.city_name} ({self.city_code})"
