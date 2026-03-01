# Utils Functions
from datetime import datetime

from Booking.models import City
from Markup.models import TykttMarkUp


def calculate_markup_fee(flight_data, markup_rules):
    """
    Calculate the total price after applying markup fees based on the model settings.

    Parameters:
        flight_data (dict): The flight offer data from the request.
        markup_rules (QuerySet): A queryset of MarkupRuleTyktt models containing markup settings.

    Returns:
        float: The total price after applying markup.
    """
    base_fare = float(flight_data["price"]["base"])  # Extract base fare from the flight data
    total_price = base_fare

    carrier_code = flight_data["itineraries"][0]["segments"][0]["carrierCode"]
    validating_carrier = flight_data["validatingAirlineCodes"][0]
    cabin_class = flight_data["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"]
    fare_type = flight_data["pricingOptions"]["fareType"][0].lower()
    passenger_type = flight_data["travelerPricings"][0]["travelerType"].lower()
    from_country = flight_data["itineraries"][0]["segments"][0]["departure"]["iataCode"]
    to_country = flight_data["itineraries"][0]["segments"][0]["arrival"]["iataCode"]

    # Iterate over all applicable markup rules
    for rule in markup_rules:
        # Check carrier rules (Marketing, Operating, Validating)
        if carrier_code in rule.marketing_carrier.split(',') or \
                carrier_code in rule.operating_carrier.split(',') or \
                validating_carrier in rule.validating_carrier.split(','):

            # Check fare type
            if fare_type in rule.fare_type.split(','):
                # Check passenger type
                if passenger_type in rule.passenger_type.split(','):
                    # Check cabin class
                    if cabin_class in rule.cabin_classes.split(','):
                        # Check country rules
                        if from_country in rule.from_country.split(',') and to_country in rule.to_country.split(','):

                            # Apply markup based on type (percentage or fixed)
                            if rule.account_type == 'percentage':
                                markup_amount = (float(rule.markup_amount) / 100) * base_fare
                            else:
                                markup_amount = float(rule.markup_amount)

                            # Update the total price
                            total_price += markup_amount

    return total_price


def calculate_markup_fee_v3(flight_data, markup_rules, office_id):
    """
    Calculate the total price after applying markup fees based on the model settings for the given flight data.

    Parameters:
        flight_data (dict): The flight offer data from the request.
        markup_rules (QuerySet): A queryset of MarkupRuleTyktt models containing markup settings.

    Returns:
        float: The total price after applying markup.
    """
    base_fare = float(flight_data["price"]["base"])  # Extract base fare from the flight data
    total_price = 0

    # Extract relevant data from the flight offer
    carrier_code = flight_data["itineraries"][0]["segments"][0]["carrierCode"]
    operating_airline = flight_data["itineraries"][0]["segments"][0]["operating"]['carrierCode']
    validating_carrier = flight_data["validatingAirlineCodes"][0]
    fare_type = flight_data["pricingOptions"]["fareType"][0].lower()
    passenger_type = flight_data["travelerPricings"][0]["travelerType"].lower()
    from_country = flight_data["itineraries"][0]["segments"][0]["departure"]["iataCode"]
    to_country = flight_data["itineraries"][0]["segments"][0]["arrival"]["iataCode"]
    departure_date = flight_data['itineraries'][0]['segments'][0]['departure']['at'].split("T")[0]
    departure_date_only = datetime.strptime(departure_date, '%Y-%m-%d').date()

    # Retrieve country codes for departure and arrival cities
    countries_from = City.objects.filter(airport_code=from_country).first()
    countries_to = City.objects.filter(airport_code=to_country).first()

    if countries_from:
        from_country_code = countries_from.country_code
    else:
        from_country_code = ''

    if countries_to:
        to_country_code = countries_to.country_code
    else:
        to_country_code = ''

    # Iterate over all applicable markup rules
    for rule in markup_rules:
        if office_id in rule.office_id.split(',') or rule.office_id == "":
            if carrier_code in rule.marketing_carrier.split(',') or rule.marketing_carrier == "":
                if operating_airline in rule.operating_carrier.split(',') or rule.operating_carrier == "":
                    if fare_type in rule.fare_type.split(',') or rule.fare_type.split(',') is None:
                        if rule.departure_date_after is None or departure_date_only > rule.departure_date_after:
                            # Exclude condition
                            if carrier_code not in rule.exclude_marketing_carrier.split(',') or carrier_code not in rule.exclude_operating_carrier.split(',') or \
                               rule.exclude_marketing_carrier == "" and rule.exclude_operating_carrier == "":
                                for travellers in flight_data['travelerPricings']:
                                    if travellers['fareDetailsBySegment'][0]['cabin'].lower() in rule.cabin_classes.split(',') or \
                                            rule.cabin_classes == "":
                                        if travellers['fareDetailsBySegment'][0]['cabin'].lower() not in rule.exclude_booking_classes or rule.exclude_booking_classes == '':
                                            if travellers['fareDetailsBySegment'][0]['class'] == rule.booking_class_of_service or rule.booking_class_of_service == "":
                                                if travellers['fareDetailsBySegment'][0]['class'] != rule.exclude_booking_class_of_service or rule.exclude_booking_class_of_service == "":
                                                    if passenger_type in rule.passenger_type.split(',') or rule.passenger_type == "":
                                                        # Check country and city together
                                                        if (from_country in rule.from_city.split(',') or from_country_code in rule.from_country.split(',') or rule.from_city == "" or rule.from_country == ""):
                                                            if (from_country not in rule.exclude_from_city.split(',') and from_country_code not in rule.exclude_from_country.split(',')) or \
                                                                (rule.exclude_from_city == "" and rule.exclude_from_country == ""):
                                                                if (to_country in rule.to_city.split(',') or to_country_code in rule.to_country.split(',') or rule.to_city == "" or rule.to_country == ""):
                                                                    if (to_country not in rule.exclude_to_city.split(',') and to_country_code not in rule.exclude_to_country.split(',')) or \
                                                                        (rule.exclude_to_city == "" and rule.exclude_to_country == ""):
                                                                        # Apply markup or discount
                                                                        if rule.markup_type in ['discount', 'promotional_discount']:
                                                                            if rule.account_type == 'percentage':
                                                                                markup_amount = (float(rule.markup_amount) / 100) * float(
                                                                                    travellers['price']['base'])
                                                                                ten_percent = markup_amount * 0.10
                                                                                markup_amount = markup_amount - ten_percent
                                                                            else:
                                                                                markup_amount = float(rule.markup_amount)
                                                                            total_price -= markup_amount
                                                                        else:
                                                                            if rule.account_type == 'percentage':
                                                                                markup_amount = (float(rule.markup_amount) / 100) * float(
                                                                                    travellers['price']['base'])
                                                                            else:
                                                                                markup_amount = float(rule.markup_amount)
                                                                            total_price += markup_amount
    return total_price


def calculate_company_markup(flight_data, markup_rules, sub_agent):
    """
    Calculate the total price after applying company markup based on the MarkupRuleCompany model.

    Parameters:
        flight_data (dict): The flight offer data from the request.
        markup_rules (QuerySet): A queryset of MarkupRuleCompany models containing markup settings.

    Returns:
        float: The grand total after applying markup.
    """
    total_price = 0.00
    from_country_code = flight_data["itineraries"][0]["segments"][0]["departure"]["iataCode"]
    to_country_code = flight_data["itineraries"][0]["segments"][0]["arrival"]["iataCode"]

    # Fetch both cities in a single query
    cities = City.objects.filter(airport_code__in=[from_country_code, to_country_code])

    # Extract country codes
    from_country = ''
    to_country = ''
    for city in cities:
        if city.city_code == from_country_code:
            from_country = city.country_code
        if city.city_code == to_country_code:
            to_country = city.country_code

    # Iterate over applicable company markup rules
    for rule in markup_rules:
        # Check if the rule applies to a local flight (same country)
        if rule.markup_type == 'local_flight' and "ng" == to_country.lower():
            for traveller in flight_data['travelerPricings']:
                if not rule.passenger or str(traveller.get("travelerType", "")).replace('HELD_', '').lower() in rule.passenger.split(','):
                    if not rule.cabin_classes or traveller['fareDetailsBySegment'][0]['cabin'].lower() in rule.cabin_classes.split(','):
                        if rule.rate_type == 'percentage':
                            markup_amount = (float(rule.value) / 100) * float(traveller['price']['base'])
                        else:
                            markup_amount = float(rule.value)
                        total_price += markup_amount

        # Check if the rule applies to an international flight (different countries)
        elif rule.markup_type == 'international_flight' and "ng" != to_country.lower():
            for traveller in flight_data['travelerPricings']:
                if not rule.passenger or str(traveller.get("travelerType", "")).replace('HELD_', '').lower() in rule.passenger.split(','):
                    if not rule.cabin_classes or traveller['fareDetailsBySegment'][0]['cabin'].lower() in rule.cabin_classes.split(','):
                        if rule.rate_type == 'percentage':
                            markup_amount = (float(rule.value) / 100) * float(traveller['price']['base'])
                        else:
                            markup_amount = float(rule.value)
                        total_price += markup_amount

        elif rule.markup_type == 'sub_agent':
            if rule.sub_agent == sub_agent:
                for traveller in flight_data['travelerPricings']:
                    if not rule.passenger or str(traveller.get("travelerType", "")).replace('HELD_', '').lower() in rule.passenger.split(','):
                        if not rule.cabin_classes or traveller['fareDetailsBySegment'][0]['cabin'].lower() in rule.cabin_classes.split(','):
                            if rule.rate_type == 'percentage':
                                markup_amount = (float(rule.value) / 100) * float(traveller['price']['base'])
                            else:
                                markup_amount = float(rule.value)
                            total_price += markup_amount
    return total_price


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
            seg.get("operating", {}).get("carrierCode", None)
            for seg in segments
            if seg.get("operating") and seg.get("operating", {}).get("carrierCode", None) != carrier_code
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

