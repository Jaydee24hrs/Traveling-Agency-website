import asyncio
import csv
import json
import logging
import os
import re
from django.http import JsonResponse
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from xhtml2pdf import pisa
from django.core.mail import send_mail
from Markup.models import ExchangeRate, MarkupRuleTyktt
from Transaction.models import ManualPayment, PayStackTransaction, Pay_small_small, FlutterwaveTransaction
from User.models import CustomUser
from User.models import Customer
from .flightbooking import AmadeusAPI
from .models import City, Booking
from .utils import calculate_company_markup, calculate_markup_fee_new
from Transaction.paystack_integration import Paystack
from email.utils import formataddr
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# Create your views here.
def create_booking_json(request):
    travel_type = request.POST.get('travel_type')
    travelClass = request.POST.get('flight_type')
    # flexible = request.POST.get('flexible')
    travel_class_list = []
    origin = request.POST.get('origin')
    destination = request.POST.get('destination')
    departureDate = request.POST.get('departureDate')
    returnDate = request.POST.get('ReturnDate')
    cabinRestrictions =  []

    originDestinations = []
    if travel_type == 'oneway':
        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {
                    "date": departureDate,
                }
            }
        )
        cabinRestrictions.append(
        {
          "cabin": request.POST.get(f'flight_type'),
          "coverage": "MOST_SEGMENTS",
          "originDestinationIds": [
            "1"
          ]
          }
         )
    elif travel_type == 'round_trip':
        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {
                    "date": departureDate
                }
            }
        )
        cabinRestrictions.append(
        {
          "cabin": request.POST.get(f'flight_type'),
          "coverage": "MOST_SEGMENTS",
          "originDestinationIds": [
            "1"
          ]
          }
         )
        originDestinations.append(
            {
                "id": "2",
                "originLocationCode": destination,
                "destinationLocationCode": origin,
                "departureDateTimeRange": {
                    "date": returnDate
                }
            }
        )
        cabinRestrictions.append(
        {
          "cabin": request.POST.get(f'flight_type'),
          "coverage": "MOST_SEGMENTS",
          "originDestinationIds": [
            "2"
          ]
          }
         )
    elif travel_type == 'multiple':
        cabinRestrictions.append(
        {
          "cabin": request.POST.get(f'flight_type'),
          "coverage": "MOST_SEGMENTS",
          "originDestinationIds": [
            "1"
          ]
          }
         )
        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {
                    "date": departureDate
                }
            }
        )
        for i in range(6):
            origin = request.POST.get(f'origin_{i}')
            destination = request.POST.get(f'destination_{i}')
            departureDate = request.POST.get(f'departureDate_{i}')
            if origin and destination and departureDate:
                cabinRestrictions.append({
                                    "cabin": request.POST.get(f'flight_type_{i}'),
                                    "coverage": "MOST_SEGMENTS",
                                    "originDestinationIds": [
                                        str(len(originDestinations) + 1)
                                    ]})
                originDestinations.append(
                    {
                        "id": str(len(originDestinations) + 1),
                        "originLocationCode": origin,
                        "destinationLocationCode": destination,
                        "departureDateTimeRange": {
                            "date": departureDate
                        }
                    }
                )

    adults = request.POST.get('adults')
    child = request.POST.get('child')
    infants = request.POST.get('infants')
    travelers = []
    current_id = 1

    for i in range(1, int(adults) + 1):
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "ADULT",
                "fareOptions": [
                    "STANDARD"
                ],
                "travelClass": travelClass
            }
        )
        current_id += 1

    for i in range(1, int(child) + 1):
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "CHILD",
                "fareOptions": [
                    "STANDARD"
                ],
                "travelClass": travelClass
            }
        )
        current_id += 1

    for i in range(1, int(infants) + 1):
        # Rotate through adults for associatedAdultId
        associated_adult_id = (i - 1) % int(adults) + 1
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "HELD_INFANT",
                "fareOptions": [
                    "STANDARD"
                ],
                "associatedAdultId": f"{associated_adult_id}",
                "travelClass": travelClass
            }
        )
        current_id += 1

    data = {
        'originDestinations': originDestinations,
        'travelers': travelers,
        "travelClass": travelClass,
        "travelClassList": travel_class_list,
        "cabinRestrictions": cabinRestrictions,
    }
    return data


def get_currency_exchnage_rate(currency):
    exchange_rate = ExchangeRate.objects.filter(currency=currency).first()
    if exchange_rate:
        return exchange_rate.rate
    return 1.0


def converter_data(office_id):
    exchange_rate = (
        ExchangeRate.objects
        .filter(office_id=office_id)
        .order_by("id")  # Ensures sorting by ID in ascending order
        .first()
    )
    if exchange_rate:
        return float(exchange_rate.rate)
    return 1.0

def send_email_booking_email(request, recipient_email, booking, emil_template):
    """
    Sends booking details extracted from the response data as an email with styled content.
    
    Parameters:
    - response_data (dict): The booking data containing flight offers, travelers, etc.
    - recipient_email (str): The email address to send the booking information to.
    - booking (object): The booking object, which might include formatted ID or other details.
    """
    # Account details mapping by currency
    account_details = {
        "NGN": [
        {
            "bank_name": "United Bank For Africa",
            "account_number": "1020904570",
            "account_name": "JOMIVIC TRAVELS AGENCY"
        },
        {
            "bank_name": "Zenith Bank PLC",
            "account_number": "1014149141",
            "account_name": "JOMIVIC TRAVELS AGENCY"
        }
        ],
        # "USD": [
        #     {
        #         "bank_name": "Providus Bank",
        #         "account_number": "1305576867",
        #         "account_name": "JOMIVIC TRAVELS AGENCY"
        #     }
        # ]
    }


    # Get account details based on booking currency
    currency = booking.currency
    # if booking.flight_data.get('is_converted') or booking.currency == "GHS":
    currency = "NGN"

    to_multiply = 1.00
    conversion_rate = 1
    conversion_rate = converter_data(booking.office_id)
    total_base_fare = 0
    total_tax_and_fees = 0
    total_amount = 0
    total_amount_price = 0
    taxes_by_traveler = {}
    travelers_table = {
        'dateOfBirth': False,
        'loyaltyPrograms': False,
        'documents': False,
        'tickets': False
    }
    for traveler in booking.response.get('data', {}).get('travelers', []):
        if 'dateOfBirth' in traveler:
            travelers_table['dateOfBirth'] = True
        if 'loyaltyPrograms' in traveler:
            travelers_table['loyaltyPrograms'] = True
        if 'documents' in traveler:
            travelers_table['documents'] = True

    if booking.response.get('data', {}).get('tickets', []):
        travelers_table['tickets'] = True

    for offer in booking.response.get('data', {}).get('flightOffers', []):
        amount = float(offer.get('price', {}).get('grandTotal', 0))
        if booking.new_flight_price:
            amount = float(booking.new_flight_price.get('price', {}).get('grandTotal', 0))
        total_amount_price = amount * conversion_rate

        # markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        markups = []

        if booking.new_flight_price :
            amount_to_add = 0.00
            amount_to_add_2 = calculate_company_markup(booking.new_flight_price, markups, booking.user)
            amount_to_add = calculate_markup_fee_new(booking.new_flight_price,
                                                         booking.office_id)

            # if markups:
            # amount_to_add_2 += calculate_company_markup(booking.new_flight_price, booking.user)

            all_amount_travelers = amount_to_add / len(booking.new_flight_price.get('travelerPricings', []))
            all_amount_travelers_2 = amount_to_add_2 / len(booking.new_flight_price.get('travelerPricings', []))
            for traveler_pricing in booking.new_flight_price.get('travelerPricings', []):
                traveler_id = traveler_pricing.get('travelerId')
                taxes = traveler_pricing.get('price', {}).get('taxes', [])
                total_taxes = sum(float(tax.get('amount', 0)) for tax in taxes)


                # Convert taxes to the selected currency
                converted_total_taxes = total_taxes * conversion_rate
                base_fare = float(traveler_pricing.get('price', {}).get('base', 0)) + all_amount_travelers
                total_fare = float(traveler_pricing.get('price', {}).get('total', 0)) + all_amount_travelers

                # Calculate converted fares
                converted_base_fare = (base_fare * conversion_rate) + all_amount_travelers_2
                converted_total_fare = (total_fare * conversion_rate) + all_amount_travelers_2
                converted_base_fare_tyktt = base_fare * conversion_rate
                converted_total_fare_tyktt = total_fare * conversion_rate

                if traveler_id not in taxes_by_traveler:
                    taxes_by_traveler[traveler_id] = {
                        'total_taxes': converted_total_taxes,
                        'converted_base_fare': converted_base_fare,
                        'converted_total_fare': converted_total_fare,
                        'converted_base_fare_tyktt': converted_base_fare_tyktt,
                        'converted_total_fare_tyktt': converted_total_fare_tyktt,
                    }
                else:
                    taxes_by_traveler[traveler_id]['total_taxes'] += converted_total_taxes
                    taxes_by_traveler[traveler_id]['converted_base_fare'] += converted_base_fare
                    taxes_by_traveler[traveler_id]['converted_total_fare'] += converted_total_fare

                # Accumulate totals
                total_base_fare += converted_base_fare
                total_tax_and_fees += converted_total_taxes
                total_amount += converted_total_fare
        else:

            amount_to_add = 0.00
            amount_to_add_2 = calculate_company_markup(booking.response['data']['flightOffers'][0], markups, booking.user)
            amount_to_add = calculate_markup_fee_new(booking.response['data']['flightOffers'][0],
                                                         booking.office_id)

            # if markups:
            #     amount_to_add_2 += calculate_company_markup(booking.response['data']['flightOffers'][0], markups, booking.user)

            all_amount_travelers = amount_to_add / len(offer.get('travelerPricings', []))
            all_amount_travelers_2 = amount_to_add_2 / len(offer.get('travelerPricings', []))

            for traveler_pricing in offer.get('travelerPricings', []):
                traveler_id = traveler_pricing.get('travelerId')
                taxes = traveler_pricing.get('price', {}).get('taxes', [])
                total_taxes = sum(float(tax.get('amount', 0)) for tax in taxes)

                # Convert taxes to the selected currency
                converted_total_taxes = (total_taxes * conversion_rate) * to_multiply
                base_fare = float(traveler_pricing.get('price', {}).get('base', 0)) + all_amount_travelers
                total_fare = float(traveler_pricing.get('price', {}).get('total', 0)) + all_amount_travelers

                # Calculate converted fares
                converted_base_fare = (base_fare * conversion_rate) + (all_amount_travelers_2 * conversion_rate)
                converted_total_fare = (total_fare * conversion_rate) + (all_amount_travelers_2 * conversion_rate)
                converted_base_fare_tyktt = base_fare * conversion_rate
                converted_total_fare_tyktt = total_fare * conversion_rate

                if traveler_id not in taxes_by_traveler:
                    taxes_by_traveler[traveler_id] = {
                        'total_taxes': converted_total_taxes,
                        'converted_base_fare': converted_base_fare * to_multiply,
                        'converted_total_fare': converted_total_fare * to_multiply,
                        'converted_base_fare_tyktt': converted_base_fare_tyktt * to_multiply,
                        'converted_total_fare_tyktt': converted_total_fare_tyktt * to_multiply,
                    }
                else:
                    taxes_by_traveler[traveler_id]['total_taxes'] += converted_total_taxes 
                    taxes_by_traveler[traveler_id]['converted_base_fare'] += converted_base_fare
                    taxes_by_traveler[traveler_id]['converted_total_fare'] += converted_total_fare

                # Accumulate totals
                total_base_fare += converted_base_fare * to_multiply
                total_tax_and_fees += converted_total_taxes * to_multiply
                total_amount += converted_total_fare * to_multiply

        temp_response = booking.response
        booking.response = temp_response
    # payment_instructions = account_details.get(currency, default_account)

    # Extract flight offers and travelers
    # flight_offers = response_data.get("data", {}).get("flightOffers", [])
    # travelers = response_data.get("data", {}).get("travelers", [])

    # Construct subject and initial messages
    subject = f"Booking Confirmation for Trip ID: {booking.formatted_id}"
    plain_message = ""

    host = request.build_absolute_uri('/')
    # account_details = {}
    # logo = host + request.settings.logo.url
    # if request.settings.logo:
    #     logo = f"{host}{request.settings.logo.url.lstrip('/')}"
    # else:
    logo = f"{host}/static/img/logo.svg"
    context = {
        "booking": booking,
        # "settings": request.settings,
        "host": host,
        "logo": logo,
        "account_details": account_details,
        "currency": currency,
        'taxes_by_traveler': taxes_by_traveler,
        'total_base_fare': total_base_fare,
        'total_tax_and_fees': total_tax_and_fees,
        'total_amount': total_amount,
        'total_amount_price': total_amount_price,
    }
    html_string = render_to_string(emil_template, context)
    email_from = "jomevictravels@quickwavetech.com"
    from_email = formataddr(("Jomevic Travels", email_from))
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=recipient_email
    )
    email.extra_headers = {"Reply-To": "jomevictravels@quickwavetech.com"}
    email.attach_alternative(html_string, "text/html")
    
    email.send()



def create_booking_json_3days(request):
    travel_type = request.POST.get('travel_type')
    travelClass = request.POST.get('flight_type')

    origin = request.POST.get('origin')
    destination = request.POST.get('destination')
    departureDate = request.POST.get('departureDate')
    returnDate = request.POST.get('ReturnDate')

    originDestinations = []
    if travel_type == 'oneway':

        flexible = True
        departureDateTimeRange = {
            "date": departureDate
        }
        if flexible:
            departureDateTimeRange["dateWindow"] = "I3D"

        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": departureDateTimeRange,
            }
        )

    elif travel_type == 'round_trip':
        flexible = True
        departureDateTimeRange = {
            "date": departureDate
        }

        returnDate = {
            "date": returnDate
        }

        # Conditionally add the "dateWindow" key if 'flexible' is present
        if flexible:
            departureDateTimeRange["dateWindow"] = "I3D"
            returnDate["dateWindow"] = "I3D"

        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": departureDateTimeRange
            }
        )
        originDestinations.append(
            {
                "id": "2",
                "originLocationCode": destination,
                "destinationLocationCode": origin,
                "departureDateTimeRange": returnDate
            }
        )
    elif travel_type == 'multiple':
        originDestinations.append(
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {
                    "date": departureDate
                }
            }
        )
        for i in range(6):

            origin = request.POST.get(f'origin_{i}')
            destination = request.POST.get(f'destination_{i}')
            departureDate = request.POST.get(f'departureDate_{i}')
            if origin and destination and departureDate:
                originDestinations.append(
                    {
                        "id": str(len(originDestinations) + 1),
                        "originLocationCode": origin,
                        "destinationLocationCode": destination,
                        "departureDateTimeRange": {
                            "date": departureDate
                        }
                    }
                )

    
    adults = request.POST.get('adults')
    child = request.POST.get('child')
    infants = request.POST.get('infants')
    travelers = []
    current_id = 1

    for i in range(1, int(adults) + 1):
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "ADULT",
                "fareOptions": [
                    "STANDARD"
                ],
                "travelClass": travelClass
            }
        )
        current_id += 1

    for i in range(1, int(child) + 1):
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "CHILD",
                "fareOptions": [
                    "STANDARD"
                ],
                "travelClass": travelClass
            }
        )
        current_id += 1

    for i in range(1, int(infants) + 1):
        # Rotate through adults for associatedAdultId
        associated_adult_id = (i - 1) % int(adults) + 1
        travelers.append(
            {
                "id": f"{current_id}",
                "travelerType": "HELD_INFANT",
                "fareOptions": [
                    "STANDARD"
                ],
                "associatedAdultId": f"{associated_adult_id}",
                "travelClass": travelClass
            }
        )
        current_id += 1

    data = {
        'originDestinations': originDestinations,
        'travelers': travelers,
        "travelClass": travelClass
    }
    return data


def get_to_and_fro(request):
    origin = request.POST.get('origin')
    destination = request.POST.get('destination')
    to_ = City.objects.filter(airport_code=origin)
    des = City.objects.filter(airport_code=destination)

    if to_ and des:
        return {
            'origin': f"{to_[0].city_name} ({to_[0].airport_code})",
            'destination': f"{des[0].city_name} ({des[0].airport_code})",
        }


# Manage Bookings Starts
@login_required(login_url='signin')
def manage(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    booking = None
    user = request.user
    total_amount_price = 0
    bookings_with_converted_amounts = []


    booking = Booking.objects.all().order_by('-id')

    # elif user.private and user.is_owner:
    #     booking = Booking.objects.filter(private_company=user.private).order_by('-id')
    # elif user.private and not user.is_owner:
    #     booking = Booking.objects.filter(private_company=user.private, user=user).order_by('-id')

    # elif user.corporate_business:
    #     if user.is_owner:
    #         # booking = Booking.objects.filter(corporate_company=user.corporate_business).order_by('-id')
    #         booking = Booking.objects.filter(corporate_company=user.corporate_business).order_by('-id')
    #     elif user.access_type == 'sub agent':
    #         booking = Booking.objects.filter(corporate_company=user.corporate_business, user=user).order_by('-id')
    #     else:
    #         booking = Booking.objects.filter(corporate_company=user.corporate_business).order_by('-id')

    # converter_data = convert_currency()

    for book in booking:
        conversion_rate = converter_data(book.office_id)
        if book.response:
            price = book.response.get('data', {}).get('flightOffers', [{}])[0].get('price', {})
            amount = float(price.get('grandTotal', 0))
            converted_amount = amount * conversion_rate
            book.converted_amount = converted_amount
            bookings_with_converted_amounts.append(book)
            total_amount_price += converted_amount

    context = {
        'booking': booking,
        'total_amount_price': total_amount_price,
        'user_permissions_codenames': user_permissions_codenames,
    }

    return render(request, 'super/managebooking.html', context)


@login_required(login_url='signin')
def bookinginfo(request, booking_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    booking = get_object_or_404(Booking, id=booking_id)
    cash_transfer = None
    airlines = load_airlines(request)
    most_recent_transaction = PayStackTransaction.objects.filter(booking=booking).order_by('-date_created').first()
    transaction = PayStackTransaction.objects.filter(booking=booking).order_by('-date_created')
    fluter_wave_transaction = FlutterwaveTransaction.objects.filter(booking=booking, status="successful")
    #using prefetched_related make it faster when calling to prevent N+1
    pay_small_small = Pay_small_small.objects.filter(booking=booking).prefetch_related('manual_payments').order_by('date_created')
    total_amount_small = Pay_small_small.objects.filter(booking=booking).aggregate(Sum('amount'))['amount__sum'] or 0
    total_balance_small = Pay_small_small.objects.filter(booking=booking).aggregate(Sum('balance'))['balance__sum'] or 0
    if total_balance_small == 0:
        booking.booking_payment = "Successful"
        cash_transfer = {"Message": "Pending Cash Or Transfer for this Booking"}
    else:
        booking.booking_payment = "In progress"
    
    if not pay_small_small and not total_balance_small and not fluter_wave_transaction and not transaction and not most_recent_transaction:
        booking.booking_payment = "Pending"

    booking.save()
    acceptable_subtypes = [
        "OTHER_SERVICE_INFORMATION", 
        "KEYWORD",
        "OTHER_SERVICE",
        "CLIENT_ID",
        "ADVANCED_TICKET_TIME_LIMIT"
    ]
    user_exists = False
    user_name = booking.user_name
    user_email = booking.user_email
    user_access_type = booking.user_access_type
    user_phone = booking.user_phone
    flight_offers_d = booking.response.get('data', {}).get('flightOffers', [])
    temp_response = booking.response
    if not flight_offers_d or not flight_offers_d[0].get('price', {}):
        booking.response = booking.init_response
    if booking.user:
        user = get_object_or_404(CustomUser, id=booking.user.id)
        user_exists = True
        user_name = user.username
        user_email = user.email
        user_access_type = user.access_type
        user_phone = user.phone
    else:
        user = None

    # converter_data = convert_currency()
    office_id = booking.office_id
    conversion_rate = 1

    # Initialize variables to hold total fares
    total_base_fare = 0
    total_tax_and_fees = 0
    total_amount = 0
    total_amount_price = 0
    taxes_by_traveler = {}
    travelers_table = {
        'dateOfBirth': False,
        'loyaltyPrograms': False,
        'documents': False,
        'tickets': False
    }

    for traveler in booking.response.get('data', {}).get('travelers', []):
        if 'dateOfBirth' in traveler:
            travelers_table['dateOfBirth'] = True
        if 'loyaltyPrograms' in traveler:
            travelers_table['loyaltyPrograms'] = True
        if 'documents' in traveler:
            travelers_table['documents'] = True

    if booking.response.get('data', {}).get('tickets', []):
        travelers_table['tickets'] = True

    for offer in booking.response.get('data', {}).get('flightOffers', []):
        amount = float(offer.get('price', {}).get('grandTotal', 0))
        if booking.new_flight_price:
            amount = float(booking.new_flight_price.get('price', {}).get('grandTotal', 0))
        total_amount_price = amount * conversion_rate

        markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        markups = None

        if booking.new_flight_price :
            amount_to_add = 0.00
            amount_to_add_2 = 0.00
            amount_to_add = calculate_markup_fee_new(booking.new_flight_price,
                                                         booking.office_id)

            if markups:
                amount_to_add_2 += calculate_company_markup(booking.new_flight_price, markups, booking.user)

            all_amount_travelers = amount_to_add / len(booking.new_flight_price.get('travelerPricings', []))
            all_amount_travelers_2 = amount_to_add_2 / len(booking.new_flight_price.get('travelerPricings', []))


            for traveler_pricing in booking.new_flight_price.get('travelerPricings', []):
                traveler_id = traveler_pricing.get('travelerId')
                taxes = traveler_pricing.get('price', {}).get('taxes', [])
                total_taxes = sum(float(tax.get('amount', 0)) for tax in taxes)


                # Convert taxes to the selected currency
                converted_total_taxes = total_taxes * conversion_rate
                base_fare = float(traveler_pricing.get('price', {}).get('base', 0)) + all_amount_travelers
                total_fare = float(traveler_pricing.get('price', {}).get('total', 0)) + all_amount_travelers

                # Calculate converted fares
                converted_base_fare = (base_fare * conversion_rate) + all_amount_travelers_2
                converted_total_fare = (total_fare * conversion_rate) + all_amount_travelers_2
                converted_base_fare_tyktt = base_fare * conversion_rate
                converted_total_fare_tyktt = total_fare * conversion_rate

                if traveler_id not in taxes_by_traveler:
                    taxes_by_traveler[traveler_id] = {
                        'total_taxes': converted_total_taxes,
                        'converted_base_fare': converted_base_fare,
                        'converted_total_fare': converted_total_fare,
                        'converted_base_fare_tyktt': converted_base_fare_tyktt,
                        'converted_total_fare_tyktt': converted_total_fare_tyktt,
                    }
                else:
                    taxes_by_traveler[traveler_id]['total_taxes'] += converted_total_taxes
                    taxes_by_traveler[traveler_id]['converted_base_fare'] += converted_base_fare
                    taxes_by_traveler[traveler_id]['converted_total_fare'] += converted_total_fare

                # Accumulate totals
                total_base_fare += converted_base_fare
                total_tax_and_fees += converted_total_taxes
                total_amount += converted_total_fare
        else:

            amount_to_add = 0.00
            amount_to_add_2 = 0.00
            amount_to_add = calculate_markup_fee_new(booking.response['data']['flightOffers'][0],
                                                         booking.office_id)

            if markups:
                amount_to_add_2 += calculate_company_markup(booking.response['data']['flightOffers'][0], markups, booking.user)

            all_amount_travelers = amount_to_add / len(offer.get('travelerPricings', []))
            all_amount_travelers_2 = amount_to_add_2 / len(offer.get('travelerPricings', []))

            for traveler_pricing in offer.get('travelerPricings', []):
                traveler_id = traveler_pricing.get('travelerId')
                taxes = traveler_pricing.get('price', {}).get('taxes', [])
                total_taxes = sum(float(tax.get('amount', 0)) for tax in taxes)

                # Convert taxes to the selected currency
                converted_total_taxes = total_taxes * conversion_rate
                base_fare = float(traveler_pricing.get('price', {}).get('base', 0)) + all_amount_travelers
                total_fare = float(traveler_pricing.get('price', {}).get('total', 0)) + all_amount_travelers

                # Calculate converted fares
                converted_base_fare = (base_fare * conversion_rate) + all_amount_travelers_2
                converted_total_fare = (total_fare * conversion_rate) + all_amount_travelers_2
                converted_base_fare_tyktt = base_fare * conversion_rate
                converted_total_fare_tyktt = total_fare * conversion_rate

                if traveler_id not in taxes_by_traveler:
                    taxes_by_traveler[traveler_id] = {
                        'total_taxes': converted_total_taxes,
                        'converted_base_fare': converted_base_fare,
                        'converted_total_fare': converted_total_fare,
                        'converted_base_fare_tyktt': converted_base_fare_tyktt,
                        'converted_total_fare_tyktt': converted_total_fare_tyktt,
                    }
                else:
                    taxes_by_traveler[traveler_id]['total_taxes'] += converted_total_taxes
                    taxes_by_traveler[traveler_id]['converted_base_fare'] += converted_base_fare
                    taxes_by_traveler[traveler_id]['converted_total_fare'] += converted_total_fare

                # Accumulate totals
                total_base_fare += converted_base_fare
                total_tax_and_fees += converted_total_taxes
                total_amount += converted_total_fare

        temp_response = booking.response
        booking.response = temp_response
        if booking.status == 'Issued':
            if not pay_small_small and not total_balance_small and not fluter_wave_transaction and not transaction and not most_recent_transaction:
                booking.booking_payment = "Successful"
        # Only save the values if they haven't been set already
            if not booking.issued_total_taxes or not booking.issued_converted_base_fare or not booking.issued_converted_total_fare:
                booking.issued_total_taxes = total_tax_and_fees
                booking.issued_converted_base_fare = total_base_fare
                booking.issued_converted_total_fare = total_amount
                booking.save()


# Layover starts
    for itinerary in booking.response.get('data', {}).get('flightOffers', [])[0].get('itineraries', []):
        segments = itinerary.get('segments', [])
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]

            # Calculate layover time between current segment and next segment
            layover_hours, layover_minutes = calculate_layover_time(
                current_segment['arrival']['at'],
                next_segment['departure']['at']
            )

            # Store layover time in the current segment
            current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

        # Ensure the last segment doesn't have a layover (since it's the end of the journey)
        segments[-1]['layover_time'] = None

    # Layover ends


    # For Seat map

    # seatmap_data = booking.seatmap 

    # if seatmap_data:
    #     seats = [seat['number'] for deck in seatmap_data['data'][0]['decks'] for seat in deck['seats']]
    # else:
    #     # Handle the None case, maybe by logging an error or providing a default value
    #     seats = []

    # # Extract unique alphabets
    # alphabets = set()
    # for seat in seats:
    #     for char in seat:
    #         if char.isalpha():
    #             alphabets.add(char.upper())
    # booking.save()
    # Include total amounts in the context
    context = {
        "booking": booking,
        "company": user,
        "user_exists": user_exists,
        'taxes_by_traveler': taxes_by_traveler,
        'total_base_fare': total_base_fare,
        'total_tax_and_fees': total_tax_and_fees,
        'total_amount': total_amount,
        'total_amount_price': total_amount_price,
        "user_name": user_name,
        "user_email": user_email,
        "user_access_type": user_access_type,
        "user_phone": user_phone,
        'travelers_table': travelers_table,
        # "seatmap_data": seatmap_data,
        # 'unique_alphabets': sorted(alphabets),
        "acceptable_subtypes": acceptable_subtypes,
        "user_permissions_codenames": user_permissions_codenames,
        'airlines': airlines,
        'most_recent_transaction': most_recent_transaction,
        'transaction': transaction,
        'pay_small_small': pay_small_small,
        'fluter_wave_transaction': fluter_wave_transaction,
        'total_amount_small': round(total_amount_small, 2),
        'total_balance_small': round(total_balance_small, 2),
        'cash_transfer':cash_transfer,
    }

    return render(request, 'super/bookinginfo.html', context)


def delete_manual_payment(request,payment_id) -> HttpResponseRedirect :
    #Retrieve manual payment instance record or return 404 if not found
    manual_payment = get_object_or_404(ManualPayment,id = payment_id)
    pay_small_small = manual_payment.Pay_small_small #paysmallsmall instance
    if request.method == 'POST':
        with db_transaction.atomic():
            #subtract the amount from "paid" and add back to balance
            pay_small_small.paid -= manual_payment.amount
            if pay_small_small.balance is not None:
                pay_small_small.balance += manual_payment.amount
            pay_small_small.save()
            #delete the manual payment record
            manual_payment.delete()
        
        messages.success(request, 'Manual payment deleted successfully')
        return redirect('bookinginfo', booking_id=pay_small_small.booking.id)
    return redirect('bookinginfo', booking_id=pay_small_small.booking.id)
    

    
def delete_pay_small_small(request,paystack_ref):
    pay_small_small = get_object_or_404(Pay_small_small,paystack__reference = paystack_ref)
    
    if request.method == 'POST':
        # with db_transaction.atomic():
        #     pay_small_small.paid -= pay_small_small.amount
        #     if pay_small_small.balance is not None:
        #         pay_small_small.balance += pay_small_small.amount
                
        #     pay_small_small.save()
        #     pay_small_small.delete()
        messages.success(request, 'paysmall small Payment deleted successfully')
        return redirect('bookinginfo', booking_id=pay_small_small.booking.id)
    return redirect('bookinginfo', booking_id=pay_small_small.booking.id)

@login_required
# @permission_required('app.delete_mostrecenttransaction', raise_exception=True)
def delete_most_recent_transaction(request, id):
    transaction = get_object_or_404(Paystack, booking=id)
    # pay_small_small = transaction.pay_small_small  # Assuming a relation exists

    if request.method == 'POST':
    #     with transaction.atomic():
    #         # Adjust the paid amount and balance_due
    #         pay_small_small.paid -= transaction.amount
    #         pay_small_small.save()

    #         transaction.delete()

    #     messages.success(request, 'Transaction deleted and balance updated successfully.')
    #     return redirect('booking_info')  # Replace with your actual redirect URL
        messages.success(request, 'most recent transaction deleted successfully')
    
        return redirect('booking_info')

def get_city_name_by_airport_code(airport_code):
    try:
        city = City.objects.get(airport_code=airport_code)
        return city.city_name
    except City.DoesNotExist:
        return None


def convert_iso8601_duration(duration):
    pattern = re.compile(r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?')
    match = pattern.match(duration)
    days, hours, minutes = match.groups()

    days = int(days) if days else 0
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0

    readable_duration = []
    if days > 0:
        readable_duration.append(f"{days}d")
    if hours > 0:
        readable_duration.append(f"{hours}hr")
    elif hours == 0 and minutes > 0:  # If there are no hours but there are minutes
        readable_duration.append("00hr")
    if minutes > 0:
        readable_duration.append(f"{minutes}min")
    elif minutes == 0 and hours > 0:  # If there are no minutes but there are hours
        readable_duration.append("00min")

    return '&nbsp'.join(readable_duration)


def set_price_range(flight_data):
    min_price = float('inf')
    max_price = float('-inf')

    for flight_id, details in flight_data.items():
        for offer in details['data']:
            price = offer.get('price', {}).get('grandTotal', '0')
            try:
                # Convert price to float instead of int
                price = float(price.replace(',', '').replace('₦', '').strip())
                min_price = min(min_price, price)
                max_price = max(max_price, price)
            except ValueError:
                # Handle the case where conversion fails
                pass

    # Default to 0 if no valid prices are found
    min_price = min_price if min_price != float('inf') else 0
    max_price = max_price if max_price != float('-inf') else 0

    return min_price, max_price


def extract_baggage_quantity(quantity):
    """Extract numeric quantity from a string."""
    if isinstance(quantity, str):
        # Extract numbers from the string
        match = re.search(r'\d+', quantity)
        if match:
            return int(match.group())
    elif isinstance(quantity, int):
        return quantity
    return 0


def convert_currency():
    default_dict = {
        "LOSN828HJ": 1.00,
    }
    return default_dict



def flight_calender(json_data):
    fare_calendar = {}

    # Convert dates from JSON data and store in fare_calendar
    for key, value in json_data.items():
        dep_date, ret_date = key.split('T')

        if dep_date not in fare_calendar:
            fare_calendar[dep_date] = {}

        # Store the price for each return date
        fare_calendar[dep_date][ret_date] = value

    # Sort the fare calendar by departure date (earliest first)
    sorted_fare_calendar = dict(sorted(fare_calendar.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))

    # Sort the return dates for each departure date
    for dep_date in sorted_fare_calendar:
        sorted_fare_calendar[dep_date] = dict(sorted(sorted_fare_calendar[dep_date].items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))
    return sorted_fare_calendar


def update_flight_prices(request, flight_type, json_data: dict) -> dict:
    markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)

    # offer['converted_price'] = "{:.2f}".format(
    #     converter_data[flight_id] * (float(offer['price']['grandTotal']) + amount_to_add) + amount_to_add_2)

    # converter_data = convert_currency()
    csv_file_path = os.path.join(settings.BASE_DIR, 'ALL_Airlines_Form_New_Site.csv')

    airline_dict = {}
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            airline_code = row['Airline Code'].strip() 
            airline_name = row['Airline Name'].strip() 
            airline_dict[airline_code] = airline_name 

    flight_prices = {}
    for office_id, value in json_data.items():
        currencies = value.get('dictionaries', {}).get('currencies', {})
        for offer in value['data']:

            amount_to_add = 0.00

            amount_to_add = calculate_markup_fee_new(offer, office_id)
            currency = offer.get('price', {}).get('currency') or offer.get('price', {}).get('billingCurrency')

            departure_date_1 = offer['itineraries'][0]['segments'][0]['departure']['at'].split('T')
            if flight_type == 'round_trip':
                departure_date_2 = offer['itineraries'][1]['segments'][0]['departure']['at'].split('T')
                go_and_come = f"{departure_date_1[0]}T{departure_date_2[0]}"
            elif flight_type == 'oneway':
                go_and_come = f"{departure_date_1[0]}"

            carrier_code = offer["itineraries"][0]["segments"][0]["carrierCode"]
            price = float(converter_data(office_id) * (float(offer['price']['grandTotal']) + amount_to_add))
            if currency and len(currencies) >= 2:
                price = float(converter_data(office_id) * (float(offer['price']['grandTotal']) + amount_to_add)) * float(get_currency_exchnage_rate(currency))
            
            airline_name = airline_dict.get(carrier_code, "Unknown Airline") 
            if go_and_come not in flight_prices:
                flight_prices[go_and_come] = {'price': price, 'airline': airline_name}
            else:
                if price < flight_prices[go_and_come].get('price', 0.0):
                    flight_prices[go_and_come] = {'price': price, 'airline': airline_name}
    if flight_type == 'round_trip':
        flight_calenders = flight_calender(flight_prices)
    elif flight_type == 'oneway':
        flight_calenders = flight_prices
    return flight_calenders


def calculate_layover_time(arrival_time, next_departure_time):
    """Calculate the layover time in hours and minutes between two segments."""
    # Parse the datetime strings (ISO 8601 format)
    arrival_dt = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
    next_departure_dt = datetime.fromisoformat(next_departure_time.replace("Z", "+00:00"))

    # Calculate the time difference (layover duration)
    layover_duration = next_departure_dt - arrival_dt
    return divmod(layover_duration.total_seconds(), 3600)

# Start 

async def fetch_flight_data(amadeus_api, travelers, originDestinations, travelClass, is_mobile, flexible_data, currency, cabinRestrictions, usd_active):
    # Run both searches concurrently
    if currency == "NGN":
        flight_data, flexibility_results = await asyncio.gather(
            amadeus_api.search_flight_v2(
                travelers=travelers,
                originDestinations=originDestinations,
                travelClass=travelClass,
                phone_search=is_mobile,
                currency=currency,
                cabinRestrictions=cabinRestrictions
            ),
            amadeus_api.search_flight_v2(
                travelers=travelers,
                originDestinations=flexible_data,
                travelClass=travelClass,
                phone_search=is_mobile,
                currency=currency,
                cabinRestrictions=cabinRestrictions
            )
        )
        if usd_active:
            flight_data_1, flexibility_results_1 = await asyncio.gather(
                amadeus_api.search_flight_v2(
                    travelers=travelers,
                    originDestinations=originDestinations,
                    travelClass=travelClass,
                    phone_search=is_mobile,
                    currency="USD",
                    cabinRestrictions=cabinRestrictions
                ),
                amadeus_api.search_flight_v2(
                    travelers=travelers,
                    originDestinations=flexible_data,
                    travelClass=travelClass,
                    phone_search=is_mobile,
                    currency="USD",
                    cabinRestrictions=cabinRestrictions
                )
            )
            combined_flight_data = {
                "LOSN828HJ" : {
                    "meta": (flight_data.get("LOSN828HJ").get("meta", {}).get("count", 0) + flight_data_1.get("LOSN828HJ").get("meta", {}).get("count", 0)),
                    "data": (flight_data.get("LOSN828HJ").get("data", []) + flight_data_1.get("LOSN828HJ").get("data", [])),
                    "dictionaries": {
                        "locations": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("locations", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("locations", {})
                        },
                        "aircraft": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("aircraft", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("aircraft", {})
                        },
                        "currencies": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("currencies", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("currencies", {})
                        },
                        "carriers": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("carriers", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("carriers", {})
                        },
                    }
                }
            }
            combined_flexibility_results = {
                "LOSN828HJ": {
                    "meta": (flexibility_results.get("LOSN828HJ").get("meta", {}).get("count", 0) + flexibility_results_1.get("LOSN828HJ").get("meta", {}).get("count", 0)),
                    "data": (flexibility_results.get("LOSN828HJ").get("data", []) + flexibility_results_1.get("LOSN828HJ").get("data", [])),
                    "dictionaries": {
                        "locations": {
                        **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("locations", {}),
                        **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("locations", {})
                        },
                        "aircraft": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("aircraft", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("aircraft", {})
                        },
                        "currencies": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("currencies", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("currencies", {})
                        },
                        "carriers": {
                            **flight_data.get("LOSN828HJ", {}).get("dictionaries", {}).get("carriers", {}),
                            **flight_data_1.get("LOSN828HJ", {}).get("dictionaries", {}).get("carriers", {})
                        },
                    }
                }
            }
            return combined_flight_data, combined_flexibility_results
        return flight_data, flexibility_results
    elif currency == "USD":
        flight_data, flexibility_results = await asyncio.gather(
            amadeus_api.search_flight_v2(
                travelers=travelers,
                originDestinations=originDestinations,
                travelClass=travelClass,
                phone_search=is_mobile,
                currency=currency,
                cabinRestrictions=cabinRestrictions
            ),
            amadeus_api.search_flight_v2(
                travelers=travelers,
                originDestinations=flexible_data,
                travelClass=travelClass,
                phone_search=is_mobile,
                currency=currency,
                cabinRestrictions=cabinRestrictions
            )
        )
        return flight_data, flexibility_results


def process_all_dat(flight_data, request):
    office_ids_with_results = set()
    markups = None
    markups_tykkt = None
    # converter_data = convert_currency()
    same_flight = {}
    delete_flight = []
    stop_counts = set()
    cabin_classes = set()
    all_cheap_air_line = {}
    baggage_options = set()
    all_stops = {}
    min_price, max_price = 0.00 , 0.00
    airlines = []
    # if request.user.private:
    #     markups = MarkupRuleCompany.objects.filter(private=request.user.private)
    # if request.user.corporate_business:
    #     markups = MarkupRuleCompany.objects.filter(corporate_business=request.user.corporate_business)
    if flight_data:
        total_count = sum(len(result.get('data', [])) for result in flight_data.values())

        if total_count > 0:

            # Add is_oneway flag to flight data
            for flight_id, details in flight_data.items():

                # For Office ID Filter
                if 'data' in details and details['data']:
                    office_ids_with_results.add(flight_id)
                
                currencies = details.get('dictionaries', {}).get('currencies', {})

                for index, offer in enumerate(details['data']):
                    itineraries = offer.get('itineraries', [])
                    amount_to_add = 0.00
                    amount_to_add_2 = 0.00
                    currency = offer.get('price', {}).get('currency') or offer.get('price', {}).get('billingCurrency')
                    if markups:
                        amount_to_add_2 += calculate_company_markup(offer, markups, request.user)

                    # if markups_tykkt:
                    amount_to_add += calculate_markup_fee_new(offer, flight_id)
                    
                    offer['converted_price'] = "{:.2f}".format(converter_data(flight_id) * (
                                float(offer['price']['grandTotal']) + amount_to_add) + amount_to_add_2)
                    if currency and len(currencies) >= 2:
                        offer['converted_price'] ="{:.2f}".format(float( get_currency_exchnage_rate(currency)) * float(offer['converted_price']))
                    offer['is_oneway'] = len(itineraries) == 1
                    offer['is_multicity'] = len(itineraries) > 2

                    # flight_check = get_check_dublicate(offer, flight_id, index)
                    # key = next(iter(flight_check))
                    # if same_flight.get(key):
                    #     if float(same_flight[key]['price']) > float(flight_check[key]['price']):
                    #         # Add current entry to delete_flight before replacing it
                    #         delete_flight.append(
                    #             f"{same_flight[key]['flight_id']}-{same_flight[key]['index']}"
                    #         )
                    #         # Update only the entry for the specific key
                    #         same_flight[key] = flight_check[key]

                    #     else:
                    #         # Add the new flight_check entry to delete_flight since it's not replacing
                    #         delete_flight.append(
                    #             f"{flight_check[key]['flight_id']}-{flight_check[key]['index']}"
                    #         )

                    # else:
                    #     same_flight.update(flight_check)
        if flight_data:
            delete_flight = set(delete_flight)
            for offer in delete_flight:
                flight_id, index = offer.split('-')
                index = int(index)  # Convert index to integer

                # Check if flight_id exists in data_structure and if index is within bounds
                if flight_id in flight_data and index < len(flight_data[flight_id]["data"]):
                    # Remove the item at the specified index
                    del flight_data[flight_id]["data"][index]

    if flight_data:
        total_count = sum(len(result.get('data', [])) for result in flight_data.values())
        if total_count > 0:

            # Add is_oneway flag to flight data
            for flight_id, details in flight_data.items():

                for index, offer in enumerate(details['data']):
                    itineraries = offer.get('itineraries', [])

                    for itinerary in itineraries:
                        # Convert duration
                        # Convert itinerary duration to readable format
                        itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])

                        # Access the first and last segments only once
                        segments = itinerary['segments']
                        first_segment = segments[0]
                        last_segment = segments[-1]

                        # Extract origin and destination airport codes
                        origin_code = first_segment['departure']['iataCode']
                        destination_code = last_segment['arrival']['iataCode']

                        # Use a caching mechanism for city name lookups
                        city_name_cache = {}

                        # Fetch or cache origin city name
                        if origin_code not in city_name_cache:
                            city_name_cache[origin_code] = get_city_name_by_airport_code(origin_code)
                        origin_city_name = city_name_cache[origin_code]

                        # Fetch or cache destination city name
                        if destination_code not in city_name_cache:
                            city_name_cache[destination_code] = get_city_name_by_airport_code(destination_code)
                        destination_city_name = city_name_cache[destination_code]

                        # Append city names to itinerary
                        itinerary['origin_city_name'] = origin_city_name
                        itinerary['destination_city_name'] = destination_city_name

                        # Calculate layover for multi-segment flights
                        segments = itinerary['segments']
                        for i in range(len(segments) - 1):
                            current_segment = segments[i]
                            next_segment = segments[i + 1]

                            # Calculate layover time between current segment and next segment
                            layover_hours, layover_minutes = calculate_layover_time(
                                current_segment['arrival']['at'],
                                next_segment['departure']['at']
                            )

                            # Store layover time in the current segment
                            current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                        # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                        segments[-1]['layover_time'] = None

                        # Precompute city names for departure and arrival airport codes
                        city_names_cache = {
                                               segment['departure']['iataCode']: get_city_name_by_airport_code(
                                                   segment['departure']['iataCode'])
                                               for segment in segments
                                           } | {
                                               segment['arrival']['iataCode']: get_city_name_by_airport_code(
                                                   segment['arrival']['iataCode'])
                                               for segment in segments
                                           }

                        # Process each segment
                        for segment in segments:
                            # Convert duration to readable format
                            segment['readable_duration'] = convert_iso8601_duration(segment['duration']) if segment.get(
                                'duration') else 'N/A'

                            # Fetch precomputed city names
                            segment['departure_city_name'] = city_names_cache[segment['departure']['iataCode']]
                            segment['arrival_city_name'] = city_names_cache[segment['arrival']['iataCode']]

                    # for Stops Filter
                    for itinerary in itineraries:
                        stop_counts.add(len(itinerary.get('segments', [])) - 1)

                    # For Cabin  Filter
                    cabin_classes |= {
                        fareDetail.get('cabin', 'Economy')
                        for itinerary in itineraries
                        for segment in itinerary.get('segments', [])
                        for traveler in offer['travelerPricings']
                        for fareDetail in traveler['fareDetailsBySegment']
                        if fareDetail['segmentId'] == segment['id']
                    }

                    #  For Baggages Filter
                    baggage_options |= {
                        extract_baggage_quantity(fareDetail.get('includedCheckedBags', {}).get('quantity', '0'))
                        for itinerary in itineraries
                        for segment in itinerary.get('segments', [])
                        for traveler in offer['travelerPricings']
                        for fareDetail in traveler['fareDetailsBySegment']
                        if fareDetail['segmentId'] == segment['id']
                    }

                    carrier_code = offer["itineraries"][0]["segments"][0]["carrierCode"]
                    num_segments = len(offer["itineraries"][0]["segments"])
                    converted_price = float(offer['converted_price'])

                    if carrier_code in all_cheap_air_line:
                        # Update price and associated data if the current price is lower
                        cheap_airline = all_cheap_air_line[carrier_code]
                        if converted_price < float(cheap_airline['price']):
                            cheap_airline.update({
                                'price': converted_price,
                                'data': offer,
                                'dictionaries': details['dictionaries']
                            })
                        # Add the offer if the stop count is new
                        if num_segments not in all_stops[carrier_code]:
                            cheap_airline['offers'].append(offer)
                            all_stops[carrier_code].append(num_segments)
                    else:
                        # Initialize data for a new carrier
                        all_stops[carrier_code] = [num_segments]
                        all_cheap_air_line[carrier_code] = {
                            'price': converted_price,
                            'data': offer,
                            'offers': [offer],
                            'dictionaries': details['dictionaries']
                        }

            all_cheap_air_line = dict(sorted(all_cheap_air_line.items(), key=lambda item: float(item[1]['price'])))
            min_price, max_price = set_price_range(flight_data)

            airlines = set()
            # Initialize airlines set
            airlines = {
                details['dictionaries']['carriers'][segment['carrierCode']]
                for flight_id, details in flight_data.items()
                if 'dictionaries' in details and 'carriers' in details['dictionaries']
                for offer in details['data']
                for itinerary in offer.get('itineraries', [])
                for segment in itinerary.get('segments', [])
                if (carrier_code := segment.get('carrierCode')) in details['dictionaries']['carriers']
            }

    to_and_fro = get_to_and_fro(request)

    return (flight_data, to_and_fro, total_count, all_cheap_air_line, min_price, max_price, all_stops, airlines,
            office_ids_with_results, stop_counts, cabin_classes, baggage_options)


def process_all_flight_flexibility(request, travel_type, flexibility_results):
    flexibility_results = update_flight_prices(request, travel_type, flexibility_results)
    minimum_price = ""
    # Iterate over the nested dictionaries to find the smallest price
    for outer_date, inner_data in flexibility_results.items():
        for inner_date, details in inner_data.items():
            if minimum_price == "":
                minimum_price = details['price']
            elif float(details['price']) < float(minimum_price):
                minimum_price = details['price']

    return flexibility_results, minimum_price


# End 

# @login_required(login_url='signin')
def flight_search(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    usd_active = ExchangeRate.objects.using("default").filter(status=True, currency="USD").exists()
    if request.method == "POST":
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = False
        # Check if the request comes from a mobile device
        if 'Mobi' in user_agent or 'Android' in user_agent:
            is_mobile = True
        currency = request.POST.get('currency_input')
        markups = None
        markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        flight_data = None
        total_count = 0
        stop_counts = set()
        cabin_classes = set()
        min_price = None
        max_price = None
        office_ids_with_results = set()
        airlines = []
        baggage_options = []
        all_cheap_air_line = {}
        all_stops = {}
        data = create_booking_json(request)
        # converter_data = convert_currency()
        amadeus_api = AmadeusAPI()
        travelers = data['travelers']
        originDestinations = data['originDestinations']
        cabinRestrictions = data['cabinRestrictions']
        travelClass = request.POST.get('flight_type')
        origin_display = request.POST.get('origin_display')
        destination_display = request.POST.get('destination_display')
        travel_type = request.POST.get('travel_type')
        flexibility_results = None
        flexibility_results_2 = request.POST.get('flexible')
        first_item = None
        minimum_price = None
        flexible = True
        
        
        if travel_type == 'round_trip' and flexibility_results_2:
            flexible_data = create_booking_json_3days(request)['originDestinations']

            flight_data, flexibility_results = asyncio.run(
                fetch_flight_data(
                    amadeus_api, travelers, originDestinations,
                    travelClass, is_mobile, flexible_data,
                    currency, cabinRestrictions,  # Correct order
                    usd_active
                )
            )
            flexibility_results, minimum_price = process_all_flight_flexibility(request, travel_type,
                                                                                flexibility_results)
        
            # flexibility_results = asyncio.run(
            #     amadeus_api.search_flight_v2(travelers=travelers, originDestinations=flexible_data,
            #                                  travelClass=travelClass, phone_search=is_mobile, currency=currency, cabinRestrictions=cabinRestrictions))
            
            # flexibility_results = update_flight_prices(request, travel_type, flexibility_results)
            # minimum_price = ""
            # # Iterate over the nested dictionaries to find the smallest price
            # for outer_date, inner_data in flexibility_results.items():
            #     for inner_date, details in inner_data.items():
            #         if minimum_price == "":
            #             minimum_price = details['price']
            #         elif float(details['price']) < float(minimum_price):
            #             minimum_price = details['price']
                        
        elif travel_type == "oneway" and flexibility_results_2:
            # flexible_data = create_booking_json_3days(request)['originDestinations']
            
            # flexibility_results = asyncio.run(
            #     amadeus_api.search_flight_v2(travelers=travelers, originDestinations=flexible_data,
            #                                  travelClass=travelClass, phone_search=is_mobile, currency=currency,  cabinRestrictions=cabinRestrictions))
            
            # flexibility_results = update_flight_prices(request, travel_type, flexibility_results)
            # # Find the date with the cheapest price
            # if flexibility_results:
            #     cheapest_date = min(flexibility_results, key=lambda date: flexibility_results[date]['price'])
            #     cheapest_flight = flexibility_results[cheapest_date]
            #     minimum_price = cheapest_flight['price']
            flexible_data = create_booking_json_3days(request)['originDestinations']
            flight_data, flexibility_results = asyncio.run(
                fetch_flight_data(
                    amadeus_api, travelers, originDestinations,
                    travelClass, is_mobile, flexible_data,
                    currency, cabinRestrictions,
                    usd_active
                )
            )
            flexibility_results = update_flight_prices(request, travel_type, flexibility_results)
            flexibility_results = dict(sorted(flexibility_results.items()))

            # Find the date with the cheapest price
            if flexibility_results:
                cheapest_date = min(flexibility_results, key=lambda date: flexibility_results[date]['price'])
                cheapest_flight = flexibility_results[cheapest_date]
                minimum_price = cheapest_flight['price']
        
        else:
        
        # flight_data = asyncio.run(
        #     amadeus_api.search_flight_v2(travelers=travelers, originDestinations=originDestinations, travelClass=travelClass, phone_search=is_mobile, currency=currency,  cabinRestrictions=cabinRestrictions))
            flexible_data = create_booking_json_3days(request)['originDestinations']
        
            flight_data, flexibility_results = asyncio.run(
                fetch_flight_data(
                    amadeus_api, travelers, originDestinations,
                    travelClass, is_mobile, flexible_data,
                    currency, cabinRestrictions,
                    usd_active
                )
            )


        if flight_data:
            total_count = sum(len(result.get('data', [])) for result in flight_data.values())
            if total_count > 0:

                # Add is_oneway flag to flight data
                for flight_id, details in flight_data.items():

                    # For Office ID Filter
                    if 'data' in details and details['data']:
                        office_ids_with_results.add(flight_id)
                        # details['data'] = sorted(details['data'], key=lambda offer: float(offer['price']['grandTotal']))

                    for offer in details['data']:
                        itineraries = offer.get('itineraries', [])
                        amount_to_add = 0.00
                        currencies = details.get('dictionaries', {}).get('currencies', {})
                        amount_to_add = calculate_markup_fee_new(offer, flight_id)

                        offer['converted_price'] = "{:.2f}".format(converter_data(flight_id) * (float(offer['price']['grandTotal']) + amount_to_add))

                        if currency and len(currencies) >= 2:
                            currencys = offer.get('price', {}).get('currency') or offer.get('price', {}).get('billingCurrency')
                            offer['converted_price'] = float(get_currency_exchnage_rate(currencys)) * float(offer['converted_price'])

                        offer['is_oneway'] = len(itineraries) == 1
                        offer['is_multicity'] = len(itineraries) > 2

                        for itinerary in itineraries:
                            # Convert duration
                            itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])

                            # Fetch city name for the first segment's departure
                            first_segment = itinerary['segments'][0]
                            origin_code = first_segment['departure']['iataCode']
                            origin_city_name = get_city_name_by_airport_code(origin_code)

                            # Fetch city name for the last segment's arrival
                            last_segment = itinerary['segments'][-1]
                            destination_code = last_segment['arrival']['iataCode']
                            destination_city_name = get_city_name_by_airport_code(destination_code)

                            # Append city names to itinerary
                            itinerary['origin_city_name'] = origin_city_name
                            itinerary['destination_city_name'] = destination_city_name

                            # Calculate layover for multi-segment flights
                            segments = itinerary['segments']
                            for i in range(len(segments) - 1):
                                current_segment = segments[i]
                                next_segment = segments[i + 1]

                                # Calculate layover time between current segment and next segment
                                layover_hours, layover_minutes = calculate_layover_time(
                                    current_segment['arrival']['at'],
                                    next_segment['departure']['at']
                                )

                                # Store layover time in the current segment
                                current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                            # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                            segments[-1]['layover_time'] = None


                            # Process each segment
                            for segment in segments:
                                duration = segment.get('duration', None)
                                if duration:
                                    segment['readable_duration'] = convert_iso8601_duration(duration)
                                else:
                                    # Handle the case where 'duration' is missing
                                    segment['readable_duration'] = 'N/A'
                                departure_code = segment['departure']['iataCode']
                                arrival_code = segment['arrival']['iataCode']
                                segment['departure_city_name'] = get_city_name_by_airport_code(departure_code)
                                segment['arrival_city_name'] = get_city_name_by_airport_code(arrival_code)

                        # for Stops Filter
                        for itinerary in itineraries:
                            stop_counts.add(len(itinerary.get('segments', [])) - 1)

                        # For Cabin  Filter
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            cabin_classes.add(fareDetail.get('cabin', 'Economy'))

                        #  For Baggages Filter
                        baggage_options = set()
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            quantity = fareDetail.get('includedCheckedBags', {}).get('quantity', '0')
                                            numeric_quantity = extract_baggage_quantity(quantity)
                                            baggage_options.add(numeric_quantity)
                        # add flight data
                        carrier_code = offer["itineraries"][0]["segments"][0]["carrierCode"]
                        num_segments = len(offer["itineraries"][0]["segments"])
                        converted_price = float(offer['converted_price'])

                        if carrier_code in all_cheap_air_line:
                            # Update price and associated data if the current price is lower
                            cheap_airline = all_cheap_air_line[carrier_code]
                            if converted_price < float(cheap_airline['price']):
                                cheap_airline.update({
                                    'price': converted_price,
                                    'data': offer,
                                    'dictionaries': details['dictionaries']
                                })
                            # Add the offer if the stop count is new
                            if num_segments not in all_stops[carrier_code]:
                                cheap_airline['offers'].append(offer)
                                all_stops[carrier_code].append(num_segments)
                        else:
                            # Initialize data for a new carrier
                            all_stops[carrier_code] = [num_segments]
                            all_cheap_air_line[carrier_code] = {
                                'price': converted_price,
                                'data': offer,
                                'offers': [offer],
                                'dictionaries': details['dictionaries']
                            }

                all_cheap_air_line = dict(sorted(all_cheap_air_line.items(), key=lambda item: float(item[1]['price'])))
                min_price, max_price = set_price_range(flight_data)



                min_price, max_price = set_price_range(flight_data)

                airlines = set()
                # For Airlines Filter
                for flight_id, details in flight_data.items():
                    if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                        carriers = details['dictionaries']['carriers']
                        for offer in details['data']:
                            for itinerary in offer.get('itineraries', []):
                                for segment in itinerary.get('segments', []):
                                    carrier_code = segment.get('carrierCode')
                                    if carrier_code and carrier_code in carriers:
                                        airline_name = carriers[carrier_code]
                                        airlines.add(airline_name)


                # for flight_id, details in flight_data.items():
                #     if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                #         # Get the carriers directly from the dictionaries
                #         carriers = details['dictionaries']['carriers']
                #         # Add each airline name to the airlines set
                #         for airline_name in carriers.values():
                #             airlines.add(airline_name)

        to_and_fro = get_to_and_fro(request)
    # flexibility_results = dict(sorted(flexibility_results.items(), key=lambda x: x[0]))

    context = {
        "user_permissions_codenames": user_permissions_codenames,
        "flight_data": flight_data,
        "total_count": total_count,
        "airlines": sorted(airlines),
        "travelClass": travelClass,
        "travel_type": travel_type,
        "travelers": travelers,
        "origin_display": origin_display,
        "destination_display": destination_display,
        "stop_counts": sorted(stop_counts),
        "cabin_classes": list(cabin_classes),
        "baggage_options": list(map(int, baggage_options)),
        "data": request.POST,
        "post_data": json.dumps(dict(request.POST)),
        "to_and_fro": to_and_fro,
        'min_price': min_price,
        'max_price': max_price,
        'office_ids_with_results': office_ids_with_results,
        'currency': currency,
        'all_cheap_air_line': all_cheap_air_line,
        'flexibility_results': flexibility_results,
        'flexibility_results_2': flexibility_results_2,
        'first_item': first_item,
        'minimum_price': minimum_price,
    }

    return render(request, 'super/flight_results.html', context)


def flight_booking(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    markups = None
    flight_data = {}
    office_id = None
    # converter_data = convert_currency()
    adult_count = 0
    child_count = 0
    infant_count = 0
    adult_base_fare = 0
    child_base_fare = 0
    infant_base_fare = 0
    adult_total_fare = 0
    child_total_fare = 0
    infant_total_fare = 0
    adult_tax_total = 0
    child_tax_total = 0
    infant_tax_total = 0
    flight_price_data = None
    markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
    airlines = load_airlines2()

    try:
        if request.method == "POST":
            flight_data = request.POST.get("flight")
            office_id = request.POST.get("office_id")
            airline = request.POST.get("airline")
            travel_type = request.POST.get("travel_type")
            try:
                flight_data = eval(flight_data)
            except:
                flight_data = json.loads(flight_data)
            airline = eval(airline)
            currencies = airline.get('currencies', {})
            aircraft = airline['aircraft']
            airline = airline['carriers']
            amadeus_api = AmadeusAPI(guest_office_ids=office_id)
            flight_d = amadeus_api.flight_pricing(flight_data)
            currency = "NGN"
            # currencies = airline.get('currencies', {})

            to_multiply = 1.00
            is_converted = False
            currency = flight_data.get('price', {}).get('currency') or flight_data.get('price', {}).get('billingCurrency')


            if flight_d:
                currency = flight_d['data']['flightOffers'][0]['price']['currency']
                stop_counts = set()
                cabin_classes = set()
                office_ids_with_results = set()
                baggage_options = []
                flight_price_data = flight_d['data']['flightOffers'][0]

                if currency and len(currencies) >= 2:
                    # get_currency_exchnage_rate(currency)
                    currency = "NGN"
                    to_multiply = float(get_currency_exchnage_rate(currency))
                    flight_data['is_converted'] = True # Mark the flight data as converted
                    flight_price_data['is_converted'] = True # Mark the flight data as converted
                    is_converted = True

                amount_to_add = 0.00
                amount_to_add_2 = 0.00
                if markups:
                    amount_to_add_2 += calculate_company_markup(flight_data, markups, request.user)

                amount_to_add = calculate_markup_fee_new(flight_price_data, office_id)

                all_amount_travelers = amount_to_add / len(flight_data['travelerPricings'])
                all_amount_travelers_2 = amount_to_add_2 / len(flight_data['travelerPricings'])


                # original_grand_total = float(flight_data['price']['grandTotal']) + amount_to_add
                # new_grand_total = float(flight_price_data['price']['grandTotal']) + amount_to_add
                original_grand_total = (float(flight_data["price"]["grandTotal"]) + amount_to_add) * to_multiply
                new_grand_total = (
                    (float(flight_price_data["price"]["grandTotal"]) + amount_to_add) * to_multiply
                )
                price_changed = (original_grand_total != new_grand_total)

                itineraries = flight_price_data.get('itineraries', [])

                for itinerary in itineraries:
                    # Convert duration
                    # itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])
                    # itinerary['readable_duration'] = convert_iso8601_duration(itinerary.get('duration', ''))

                    # Fetch city name for the first segment's departure
                    if itinerary.get('segments'):
                        first_segment = itinerary['segments'][0]
                        origin_code = first_segment['departure']['iataCode']
                        origin_city_name = get_city_name_by_airport_code(origin_code)

                        # Fetch city name for the last segment's arrival
                        last_segment = itinerary['segments'][-1]
                        destination_code = last_segment['arrival']['iataCode']
                        destination_city_name = get_city_name_by_airport_code(destination_code)

                        # Append city names to itinerary
                        itinerary['origin_city_name'] = origin_city_name
                        itinerary['destination_city_name'] = destination_city_name

                        itinerary.update({
                            'origin_city_name': origin_city_name,
                            'destination_city_name': destination_city_name
                        })


                        # Calculate layover for multi-segment flights
                        segments = itinerary.get('segments', [])
                        for i in range(len(segments) - 1):
                            current_segment = segments[i]
                            next_segment = segments[i + 1]

                            # Calculate layover time between current segment and next segment
                            layover_hours, layover_minutes = calculate_layover_time(
                                current_segment['arrival']['at'],
                                next_segment['departure']['at']
                            )

                            # Store layover time in the current segment
                            current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                        # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                        segments[-1]['layover_time'] = None

                    # Process each segment
                    for segment in segments:
                        duration = segment.get('duration', None)
                        if duration:
                            segment['readable_duration'] = convert_iso8601_duration(duration)
                        else:
                            # Handle the case where 'duration' is missing
                            segment['readable_duration'] = 'N/A'
                        departure_code = segment['departure']['iataCode']
                        arrival_code = segment['arrival']['iataCode']
                        segment['departure_city_name'] = get_city_name_by_airport_code(departure_code)
                        segment['arrival_city_name'] = get_city_name_by_airport_code(arrival_code)

                # for Stops Filter
                for itinerary in itineraries:
                    stop_counts.add(len(itinerary.get('segments', [])) - 1)

                # For Cabin  Filter
                for itinerary in itineraries:
                    for segment in itinerary.get('segments', []):
                        for traveler in flight_price_data.get('travelerPricings', []):
                            for fareDetail in traveler['fareDetailsBySegment']:
                                if fareDetail['segmentId'] == segment['id']:
                                    cabin_classes.add(fareDetail.get('cabin', 'Economy'))

                #  For Baggages Filter
                baggage_options = set()
                for itinerary in itineraries:
                    for segment in itinerary.get('segments', []):
                        for traveler in flight_price_data.get('travelerPricings', []):
                            for fareDetail in traveler['fareDetailsBySegment']:
                                if fareDetail['segmentId'] == segment['id']:
                                    quantity = fareDetail.get('includedCheckedBags', {}).get('quantity', '0')
                                    numeric_quantity = extract_baggage_quantity(quantity)
                                    baggage_options.add(numeric_quantity)




            to_and_fro = get_to_and_fro(request)
            conversion_rate = converter_data(office_id)
            # Calculate converted fares
            amount_to_add = 0.00
            amount_to_add_2 = 0.00
            if markups:
                amount_to_add_2 += calculate_company_markup(flight_data, markups, request.user)

            amount_to_add = calculate_markup_fee_new(flight_price_data, office_id)

            grand_total = float(flight_price_data['price']['grandTotal']) + amount_to_add
            converted_grand_total = ((grand_total * conversion_rate) + amount_to_add_2) * to_multiply

            for traveler in flight_price_data['travelerPricings']:

                base_fare = float(traveler['price']['base']) + all_amount_travelers
                total_fare = float(traveler['price']['total']) + all_amount_travelers

                taxes = traveler.get('price', {}).get('taxes', [])
                total_taxes = sum(float(tax.get('amount', 0)) for tax in taxes)

                # Convert base fare and total fare
                converted_base_fare = ((base_fare  * conversion_rate) + all_amount_travelers_2) * to_multiply
                converted_total_fare = ((total_fare * conversion_rate) + all_amount_travelers_2) * to_multiply
                converted_total_taxes = (total_taxes * conversion_rate) * to_multiply


                if traveler['travelerType'] == 'ADULT':
                    adult_count += 1
                    adult_base_fare = converted_base_fare
                    adult_total_fare = converted_total_fare
                    adult_tax_total = converted_total_taxes

                elif traveler['travelerType'] == 'CHILD':
                    child_count += 1
                    child_base_fare = converted_base_fare
                    child_total_fare = converted_total_fare
                    child_tax_total = converted_total_taxes

                elif traveler['travelerType'] == 'HELD_INFANT':
                    infant_count += 1
                    infant_base_fare = converted_base_fare
                    infant_total_fare = converted_total_fare
                    infant_tax_total = converted_total_taxes
            # json_data = json.dumps(flight_data, indent=4)
        context = {
            'user_permissions_codenames': user_permissions_codenames,
            'aircraft': aircraft,
            'currency': currency,
            'flight': flight_data,
            'flight_data': flight_data,
            'guest_office_id': office_id,
            'airline': airline,
            'airlines': airlines,
            'flight_price_data': flight_price_data,
            'travel_type': travel_type,
            'adult_count': adult_count,
            'child_count': child_count,
            'infant_count': infant_count,
            'adult_base_fare': adult_base_fare,
            'child_base_fare': child_base_fare,
            'infant_base_fare': infant_base_fare,
            'adult_total_fare': adult_total_fare,
            'child_total_fare': child_total_fare,
            'infant_total_fare': infant_total_fare,
            'adult_tax_total': adult_tax_total,
            'child_tax_total': child_tax_total,
            'infant_tax_total': infant_tax_total,
            'converted_grand_total': converted_grand_total,
            "to_and_fro": to_and_fro,
            "price_changed": price_changed,
            'office_ids_with_results': office_ids_with_results,
            "is_converted": is_converted
        }

        return render(request, 'super/flight_booking.html', context)
    except Exception as E:
        logging.error(
            f"Failed to Get Fare Rule: {E}\nError content: {E}")
        return render(request, 'super/booking_failure.html')


# def booking

def load_airlines2():
    airlines = []
    csv_file_path = os.path.join(settings.BASE_DIR, 'ALL_Airlines_Form_New_Site.csv')

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            airline_name = row.get('Airline Name')
            airline_code = row.get('Airline Code')
            airlines.append({
                'name': airline_name,
                'code': airline_code
            })
    return airlines

def search_flight_code(request):
    query = request.GET.get('query', '')
    if query:
        if len(query) <= 2:
            results = City.objects.filter(
                Q(country_code__icontains=query) |
                Q(state_code__icontains=query)
            ).order_by('airport')[:150]
        elif len(query) <= 3:
            results = City.objects.filter(
                Q(airport_code__icontains=query) |
                Q(city_code__icontains=query) |
                Q(state_code__icontains=query)
            ).order_by('airport')[:150]
        else:
            results = City.objects.filter(
                Q(city_code__icontains=query) |
                Q(city_name__icontains=query) |
                Q(country__icontains=query) |
                Q(country_code__icontains=query) |
                Q(airport__icontains=query) |
                Q(airport_code__icontains=query) |
                Q(state_code__icontains=query)
            ).order_by('airport')[:150]

        data = [{'id': result.id, 'state_code': result.state_code, 'city_code': result.city_code,
                 'city_name': result.city_name,
                 'country': result.country, 'airport': result.airport, 'country_code': result.country_code,
                 'airport_code': result.airport_code} for result in results]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def get_city_by_iata_code(request):
    iata_code = request.GET.get('iata_code', '')
    if iata_code:
        try:
            city = City.objects.get(airport_code=iata_code)
            data = {
                'city_name': city.city_name,
                'airport_name': city.airport,
            }
            return JsonResponse(data)
        except City.DoesNotExist:
            return JsonResponse({'error': 'City not found'}, status=404)
    return JsonResponse({'error': 'No IATA code provided'}, status=400)


def get_fare_rule(request):
    data_string = json.loads(request.body)
    flight_data_str = data_string['flight_data']
    guest_office_id = data_string['guest_office_id']
    json_string = re.sub(r'<script[^>]*>|</script>', '', flight_data_str)
    json_data = json.loads(json_string)
    amadeus_api = AmadeusAPI(guest_office_ids=guest_office_id)
    try:
        flight_data = amadeus_api.get_fare_rule(json_data)
        return JsonResponse(flight_data, safe=False)
    except Exception as e:
        error_content = e.response.text if e.response else str(e)
        logging.error(
            f"Failed to Get Fare Rule: {e}\nError content: {error_content}")


def create_customers(request, traveler_id):
    email = request.POST.get(f"booking_email_address_{traveler_id}")
    if not Customer.objects.filter(email=email).exists() and email:
        Customer.objects.create(
            first_name=request.POST.get(f"booking_given_name_{traveler_id}"),
            last_name=request.POST.get(f"booking_last_name_{traveler_id}"),
            email=email,
            phone_number=request.POST.get(f"booking_phone_number_{traveler_id}"),
            country_code=request.POST.get(f"country_code_{traveler_id}"),
            date_of_birth=request.POST.get(f"dob_booking_{traveler_id}"),
        )



def create_flight_data(request, booking_data=None):
    # flight_data = eval(request.POST.get("flight"))
    travellers = []
    user = request.user
    if request.POST.get("flight"):
        characters = 0
        for key, value in request.POST.items():
            characters += len(str(value))

        flight_data = eval(request.POST.get("flight"))

        email = request.POST.get(f"booking_email_address_1") or request.POST.get(f"agency_email")
        phone_code = request.POST.get(f"country_code_1") or request.POST.get(f"agency_phone_code")
        phone_num = str(request.POST.get(f"booking_phone_number_1")) or str(request.POST.get(f"agency_phone_num"))

        for traveller in flight_data['travelerPricings']:
            traveler_id = traveller['travelerId']  # Extract the travelerId

            dial_code = request.POST.get(f"hidden_dial_code_{traveler_id}")
            if dial_code and phone_num:
                phone = f"{phone_num}".replace(" ", "")
            else:
                phone = phone_num.replace(" ", "")
            if request.POST.get(f"country_code_{traveler_id}"):
                phone_code = request.POST.get(f"country_code_{traveler_id}").replace("+", "")
            # Create the structure for each traveler
            traveller_info = {
                "id": traveler_id,
                "dateOfBirth": request.POST.get(f"dob_booking_{traveler_id}"),
                "name": {
                    "firstName": request.POST.get(f"booking_given_name_{traveler_id}") + " " + request.POST.get(
                        f"booking_title_{traveler_id}"),
                    "lastName": request.POST.get(f"booking_last_name_{traveler_id}")
                },
                "gender": "UNSPECIFIED",
                "contact": {
                    "emailAddress": request.POST.get(f"booking_email_address_{traveler_id}") or email,
                    "phones": [
                        {
                            "deviceType": "MOBILE",
                            "countryCallingCode": phone_code,
                            "number": f'{phone.replace(" + ", "")}'
                        }
                    ]
                }
            }

            # Conditionally add the "documents" section
            if request.POST.get(f"program_owner_{traveler_id}") and request.POST.get(f"program_id_{traveler_id}"):
                traveller_info["loyaltyPrograms"] = [{
                    "programOwner": request.POST.get(f"program_owner_{traveler_id}"),
                    "id": request.POST.get(f"program_id_{traveler_id}")
                }]

            if request.POST.get(f"passportNumber_{traveler_id}"):
                traveller_info["documents"] = [
                    {
                        "documentType": "PASSPORT",
                        "number": request.POST.get(f"passportNumber_{traveler_id}"),
                        "expiryDate": request.POST.get(f"passportExpiryDate_{traveler_id}"),
                        "issuanceCountry": request.POST.get(f"issuanceCountry_{traveler_id}"),
                        "issuanceDate": request.POST.get(f"issuanceDate_{traveler_id}"),
                        "nationality": request.POST.get(f"nationality_{traveler_id}"),
                        "holder": True,
                        "issuanceLocation": request.POST.get(f"issuanceLocation_{traveler_id}"),
                        "birthPlace": request.POST.get(f"birthPlace_{traveler_id}")
                    }
                ]

            # Append the traveler_info to the travellers list
            travellers.append(traveller_info)
            create_customers(request, traveler_id)

    if booking_data:
        for traveller in booking_data.init_response['data']['travelers']:
            traveler_id = traveller['id']  # Extract the travelerId
            if request.POST.get(f"passportNumber_{traveler_id}"):
                gender = None
                phone = None
                # traveler_id = traveller['id']  # Extract the travelerId
                dial_code = request.POST.get(f"country_code_{traveler_id}")
                phone_number = request.POST.get(f"booking_phone_number_{traveler_id}")
                if dial_code and phone_number:
                    phone = f"{dial_code}{phone_number}".replace("+", "")
                if request.POST.get(f"gender_{traveler_id}"):
                    gender = request.POST.get(f"gender_{traveler_id}").upper()

                # Create the structure for each traveler
                traveller_info = {
                    "id": traveler_id,
                    "dateOfBirth": traveller.get('dateOfBirth'),
                    "name": {
                        "firstName": request.POST.get(f"givenName{traveler_id}") or traveller['name']['firstName'],
                        "lastName": request.POST.get(f"lastName{traveler_id}") or traveller['name']['lastName']
                    },
                    "gender": "UNSPECIFIED",
                    "contact": {
                        "emailAddress": request.POST.get(f"booking_email_address_{traveler_id}") or
                                        traveller['contact']['emailAddress'],
                        "phones": [
                            {
                                "deviceType": "MOBILE",
                                "countryCallingCode": request.POST.get(f"country_code_{traveler_id}") or
                                                      traveller['contact']['phones'][0]['countryCallingCode'],
                                "number": phone or traveller['contact']['phones'][0]['number']
                            }
                        ]
                    }
                }
                # Conditionally add the "documents" section
                if request.POST.get(f"passportNumber_{traveler_id}"):
                    traveller_info["documents"] = [
                        {
                            "documentType": request.POST.get(f"documentType_{traveler_id}"),
                            "number": request.POST.get(f"passportNumber_{traveler_id}"),
                            "expiryDate": request.POST.get(f"passportExpiryDate_{traveler_id}"),
                            "issuanceDate": request.POST.get(f"issuanceDate_{traveler_id}"),
                            "issuanceCountry": request.POST.get(f"issuanceCountry_{traveler_id}"),
                            "validityCountry": request.POST.get(f"nationality_{traveler_id}"),
                            "nationality": request.POST.get(f"nationality_{traveler_id}"),
                            "holder": True
                        }
                    ]

                # Append the traveler_info to the travellers list
                travellers.append(traveller_info)
    # Return or process travellers as needed
    return travellers


def create_flight_data_1(request, booking_data=None):
    travellers = []
    user = request.user
    if booking_data:
        for traveller in booking_data.init_response['data']['travelers']:
            traveler_id = traveller['id']  # Extract the travelerId
            gender = None
            phone = None
            dial_code = request.POST.get(f"country_code_{traveler_id}")
            phone_number = request.POST.get(f"booking_phone_number_{traveler_id}")
            if phone_number:
                phone = f"{phone_number}".replace("+", "")
            if request.POST.get(f"gender_{traveler_id}"):
                gender = request.POST.get(f"gender_{traveler_id}").upper()

            # Create the structure for each traveler
            traveller_info = {
                "id": traveler_id,
            }
            if request.POST.get(f"program_owner_{traveler_id}") and request.POST.get(f"program_id_{traveler_id}"):
                traveller_info["loyaltyPrograms"] = [{
                    "programOwner": request.POST.get(f"program_owner_{traveler_id}"),
                    "id": request.POST.get(f"program_id_{traveler_id}")
                }]

            # Append the traveler_info to the travellers list
                travellers.append(traveller_info)
    # Return or process travellers as needed
    return travellers


def create_contact_information(request):
    user = request.user
    contact = {
        "addresseeName": {
            "firstName": "Arinze",
            "lastName": "Okoh"
        },
        "companyName": "Travel Yakata",
        "purpose": "STANDARD",
        "phones": [
            {
                "deviceType": "MOBILE",
                "countryCallingCode": "234",
                "number": "9039531793"
            }
        ],
        "emailAddress": "ng@tyktt.com",
        "address": {
            "lines": [
                "lekki, lagos State"
            ],
            "postalCode": "12345",
            "cityName": "Lagos",
            "countryCode": "NG"
        }
    }

    # if user:
    #     if user.corporate_business:
    #         data = get_object_or_404(Corporate_Business, id=user.corporate_business.id)
    #         contact["companyName"] =  data.company_reg_name.split(" ")[0]
    #         contact["phones"][0]["countryCallingCode"] = data.company_phone_number_dial_code or "234"
    #         contact["phones"][0]["number"] = data.company_phone_number or "9039531793"
    #         contact["emailAddress"] = data.company_email
    #         # contact["address"]["lines"] = [data.company_address]
    #         contact["address"]["postalCode"] = data.company_postal_code or "28014"
    #         contact["address"]["cityName"] = data.company_city or "lagos"
    #     elif user.private:
    #         data = get_object_or_404(Private, id=user.private.id)
    #         contact["companyName"] = data.businessName.split(" ")[0]
    #         contact["phones"][0]["countryCallingCode"] = user.phone_number_dial_code or "234"
    #         contact["phones"][0]["number"] = user.phone or "9039531793"
    #         contact["emailAddress"] = user.email
    #         # contact["address"]["lines"] = [user.address.replace(',', '')]
    #         contact["address"]["postalCode"] = user.postal_code or "28014"
    #         contact["address"]["cityName"] = user.city or "lagos"

    return contact


def check_availability(flight_data):
    source = flight_data['source']
    travellers = []
    originDestinations = []
    includedCarrierCodes = []
    for flight in flight_data['itineraries']:
        flight_date = flight['segments'][0]['departure']['at']
        includedCarrierCodes = flight['segments'][0]['carrierCode']
        date, time = flight_date.split('T')
        od = {
            "id": 1,
            "originLocationCode": flight['segments'][0]['departure']['iataCode'],
            "destinationLocationCode": flight['segments'][0]['arrival']['iataCode'],
            "departureDateTime": {
                "date": date,
                "time": time
            }
        }
        originDestinations.append(od)
    for traveller in flight_data['travelerPricings']:
        t = {
            "id": traveller['travelerId'],
            "travelerType": traveller['travelerType']
        }
        travellers.append(t)
    return travellers, source, originDestinations, includedCarrierCodes


def create_new_flight_data(old_flight, new_flight):
    all_class_change = []
    for jp in new_flight['segments'][0]['availabilityClasses']:
        old_flight['itineraries'][0]['segments'][0]['departure'] = new_flight['segments'][0]['departure']
        old_flight['itineraries'][0]['segments'][0]['number'] = new_flight['segments'][0]['number']
        old_flight['itineraries'][0]['segments'][0]['aircraft'] = new_flight['segments'][0]['aircraft']
        old_flight['itineraries'][0]['segments'][0]['arrival'] = new_flight['segments'][0]['arrival']
        old_flight['itineraries'][0]['segments'][0]['arrival'] = new_flight['segments'][0]['arrival']
        old_flight['travelerPricings'][0]['fareDetailsBySegment'][0]['class'] = jp['class']
        all_class_change.append(old_flight)
    return all_class_change



def split_payments_with_dates(payment_case, amount, start_date):
    # Define a dictionary to map payment cases to their corresponding values
    # lll
    payment_mapping = {
        'nextday': {'percentage': 0.50, 'total_percentage': 0.05, 'end_interval_days': 1},
        'oneweek': {'percentage': 0.50, 'total_percentage': 0.10, 'end_interval_days': 7},
        'twoweek': {'percentage': 0.40, 'total_percentage': 0.15, 'end_interval_days': 14},
        'threeweek': {'percentage': 0.40, 'total_percentage': 0.20, 'end_interval_days': 21},
        'onemonths': {'percentage': 0.40, 'total_percentage': 0.25, 'end_interval_days': 30},
        'twomonths': {'percentage': 0.40, 'total_percentage': 0.30, 'end_interval_days': 60},
    }

    # Get the details based on the payment case
    payment_details = payment_mapping.get(payment_case)

    if payment_details:
        # Adjust the amount to include the total percentage
        amount += amount * payment_details['total_percentage']

        # Define initial payment details
        first_payment_percentage = payment_details['percentage']
        first_payment = amount * first_payment_percentage
        remaining_amount = amount - first_payment

        if payment_case == "nextday" or payment_case == "oneweek":
            payment_schedule = [
            {'amount': first_payment, 'due_date': start_date}  # First payment is due on the start date
        ]
            if payment_case =="oneweek":
                due_date = start_date + timedelta(days=7)
            else:
                due_date = start_date + timedelta(days=1)
            payment_schedule.append({
                'amount': remaining_amount,
                'due_date': due_date
            })

            return payment_schedule

        # Calculate the amounts for up to 3 payments
        remaining_payment = remaining_amount / 2 if remaining_amount > 0 else 0

        # Calculate interval based on end interval and number of payments (3 max)
        end_interval_days = payment_details['end_interval_days']
        interval_days = end_interval_days // 2  # Three payments spread across the total interval

        # Create a list to store payment amounts and their due dates
        payment_schedule = [
            {'amount': first_payment, 'due_date': start_date}  # First payment is due on the start date
        ]

        # Calculate due dates for each additional payment
        for i in range(1, 3):  # Limit to a max of 3 payments
            due_date = start_date + timedelta(days=interval_days * i)
            payment_schedule.append({
                'amount': remaining_payment,
                'due_date': due_date
            })

        return payment_schedule
    else:
        raise ValueError("Invalid payment case provided.")


def send_booking_email_2(response_data, recipient_email, booking):
    """
    Sends booking details extracted from the response data as an email with styled content.
    
    Parameters:
    - response_data (dict): The booking data containing flight offers, travelers, etc.
    - recipient_email (str): The email address to send the booking information to.
    - booking (object): The booking object, which might include formatted ID or other details.
    """
    # Account details mapping by currency
    account_details = {
        "NGN": [
            {"bank_name": "United Bank For Africa", "account_number": "1020904570", "account_name": "JOMIVIC TRAVELS AGENCY "}
        ],
        "USD": [
            {"bank_name": "Zenith Bank PLC ", "account_number": "1014149141", "account_name": "JOMIVIC TRAVELS AGENCY "},
        ]
    }

    # Default account if currency doesn't match
    default_account = [
         {"bank_name": "Zenith Bank PLC", "account_number": "1014149141", "account_name": "JOMIVIC TRAVELS AGENCY "}
    ]

    # Get account details based on booking currency
    currency = booking.currency
    if booking.flight_data.get('is_converted'):
        currency = "NGN"
    payment_instructions = account_details.get(currency, default_account)

    # Extract flight offers and travelers
    flight_offers = response_data.get("data", {}).get("flightOffers", [])
    travelers = response_data.get("data", {}).get("travelers", [])

    # Construct subject and initial messages
    subject = f"Booking Confirmation for Trip ID: {booking.formatted_id}"
    plain_message = f"Thank you for booking with us! Your reservation has been successfully placed. Here’s your booking reference: {booking.formatted_id}.\n\n"
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #EAEAEA; padding: 20px;">
        <h2 style="color: #FFA500;">Booking Confirmation for Trip ID: {booking.formatted_id}</h2>
        <p>Thank you for booking with us! Booking information is stated below:</p>
    """

    # Traveler Information
    plain_message += "Traveler Information:\n"
    html_message += "<h3 style='color: #007bff;'>Traveler Information:</h3>"
    for traveler in travelers:
        name = f"{traveler['name']['firstName']} {traveler['name']['lastName']}"
        email = traveler["contact"]["emailAddress"]
        plain_message += f"- {name}, Email: {email}\n"
        html_message += f"<p><strong>{name}</strong>, Email: {email}</p>"
    plain_message += "\n"

    # Flight Itineraries
    html_message += "<h3 style='color: #007bff;'>Flight Itineraries:</h3>"
    plain_message += "Flight Itineraries:\n"
    for offer in flight_offers:
        itineraries = offer.get("itineraries", [])
        total_price = offer.get("price", {}).get("total", "N/A")
        for itinerary in itineraries:
            for segment in itinerary.get("segments", []):
                departure = segment["departure"]["iataCode"]
                arrival = segment["arrival"]["iataCode"]
                departure_time = datetime.fromisoformat(segment["departure"]["at"]).strftime('%Y-%m-%d %H:%M:%S')
                flight_number = segment["carrierCode"] + segment["number"]
                plain_message += f"- Flight {flight_number} from {departure} to {arrival} on {departure_time}\n"
                html_message += f"""
                <div style='padding: 10px; background-color: #ffffff; border-radius: 8px;'>
                    <p><strong>Flight {flight_number}</strong> from {departure} to {arrival}</p>
                    <p>Departure: {departure_time}</p>
                </div>
                """
        html_message += "<hr>"
        html_message += f"<p><strong>Total Price: {currency}  {float(total_price):,.2f}</strong></p>"
    html_message += "<hr>"

    # Payment Instructions
    html_message += "<h3 style='color: #007bff;'>Payment Instructions:</h3>"
    html_message += f"""
    <p>To ensure prompt processing, kindly use your Trip ID <strong>{booking.formatted_id}</strong> as the transaction reference or depositor’s name. Below are the payment options available:</p>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    """
    for account in payment_instructions:
        html_message += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Bank Name</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['bank_name']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Account Number</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['account_number']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Account Name</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['account_name']}</td>
        </tr>
        """
    html_message += "</table></body></html>"
    from_email = formataddr(("Jomivic Travels", "jomevictravels@quickwavetech.com"))

    # Send email
    send_mail(subject, plain_message, from_email, [recipient_email], html_message=html_message)


def send_booking_email(request, response_data, recipient_email, booking):
    """
    Sends booking details extracted from the response data as an email with styled content.
    
    Parameters:
    - response_data (dict): The booking data containing flight offers, travelers, etc.
    - recipient_email (str): The email address to send the booking information to.
    - booking (object): The booking object, which might include formatted ID or other details.
    """
    # Default account if currency doesn't match
    account_details = {
        "NGN": [
        {
            "bank_name": "United Bank For Africa",
            "account_number": "1020904570",
            "account_name": "JOMIVIC TRAVELS AGENCY"
        },
        {
            "bank_name": "Zenith Bank PLC",
            "account_number": "1014149141",
            "account_name": "JOMIVIC TRAVELS AGENCY"
        }
        ],
        # "USD": [
        #     {
        #         "bank_name": "Providus Bank",
        #         "account_number": "1305576867",
        #         "account_name": "JOMIVIC TRAVELS AGENCY"
        #     }
        # ]
    }

    # Get account details based on booking currency
    currency = booking.currency
    # if booking.flight_data.get('is_converted') or booking.currency == "GHS":
    currency = "NGN"
    payment_instructions = account_details.get(currency, account_details)

    # Extract flight offers and travelers
    flight_offers = response_data.get("data", {}).get("flightOffers", [])
    travelers = response_data.get("data", {}).get("travelers", [])

    traveler_types = {}
    for offer in flight_offers:
        for pricing in offer.get('travelerPricings', []):
            traveler_id = pricing.get('travelerId')
            traveler_type = pricing.get('travelerType', 'UNKNOWN')
            traveler_types[traveler_id] = traveler_type

    # Construct subject and initial messages
    subject = f"Booking Confirmation for Trip ID: {booking.formatted_id}"
    plain_message = f"Thank you for booking with us! Your reservation has been successfully placed. Here’s your booking reference: {booking.formatted_id}.\n\n"
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #EAEAEA; padding: 20px;">
        <h2 style="color: #FFA500;">Booking Confirmation for Trip ID: {booking.formatted_id}</h2>
        <p>Thank you for booking with us! Booking information is stated below:</p>
    """

    # Traveler Information
    plain_message += "Traveler Information:\n"
    html_message += "<h3 style='color: #007bff;'>Traveler Information:</h3>"
    for traveler in travelers:
        name = f"{traveler['name']['firstName']} {traveler['name']['lastName']}"
        email = traveler["contact"]["emailAddress"]
        t_type = traveler_types.get(traveler_id, 'UNKNOWN')
        plain_message += f"- {name}, Email: {email}\n"
        html_message += f"<p><strong>{name}</strong> - ({t_type})</p>"
    plain_message += "\n"

    # Flight Itineraries
    html_message += "<h3 style='color: #007bff;'>Flight Itineraries:</h3>"
    plain_message += "Flight Itineraries:\n"
    for offer in flight_offers:
        itineraries = offer.get("itineraries", [])
        total_price = offer.get("price", {}).get("total", "0")
        # currency = offer.get("price", {}).get("currency", "NGN")
        for itinerary in itineraries:
            for segment in itinerary.get("segments", []):
                departure = segment["departure"]["iataCode"]
                arrival = segment["arrival"]["iataCode"]
                departure_time = datetime.fromisoformat(segment["departure"]["at"]).strftime('%Y-%m-%d %H:%M:%S')
                flight_number = segment["carrierCode"] + segment["number"]
                plain_message += f"- Flight {flight_number} from {departure} to {arrival} on {departure_time}\n"
                html_message += f"""
                <div style='padding: 10px; background-color: #ffffff; border-radius: 8px;'>
                    <p><strong>Flight {flight_number}</strong> from {departure} to {arrival}</p>
                    <p>Departure: {departure_time}</p>
                </div>
                """
        html_message += "<hr>"
        html_message += f"<p><strong>Total Price: {currency}  {float(booking.converted_amount):,.2f}</strong></p>"
    html_message += "<hr>"

    # Payment Instructions
    html_message += "<h3 style='color: #007bff;'>Payment Instructions:</h3>"
    html_message += f"""
    <p>To ensure prompt processing, kindly use your Trip ID <strong>{booking.formatted_id}</strong> as the transaction reference or depositor’s name. Below are the payment options available:</p>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    """
    for account in payment_instructions:
        html_message += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Bank Name</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['bank_name']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Account Number</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['account_number']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f1f1f1;">Account Name</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{account['account_name']}</td>
        </tr>
        """
    html_message += "</table></body></html>"

    ## PDF

    host = request.build_absolute_uri('/')
    # # account_details = {}
    # # logo = host + request.settings.logo.url
    # if request.settings.logo:
    #     logo = f"{host}{request.settings.logo.url.lstrip('/')}"
    # else:
    logo = f"{host}/static/img/logo.svg"
    context = {
        "booking": booking,
        # "settings": request.settings,
        "host": host,
        "logo": logo,
        "account_details": account_details,
        "currency": currency
    }
    html_string = render_to_string('emails/email_itinerary_reserved.html', context)
    # pdf_buffer = BytesIO()
    # pdf_options = {
    #     'page-size': 'A5',
    #     'orientation': 'Landscape',
    #     'margin-top': '0.5cm',
    #     'margin-right': '0.5cm',
    #     'margin-bottom': '0.5cm',
    #     'margin-left': '0.5cm',
    #     'encoding': "UTF-8",
    #     'no-outline': None,
    #     "zoom": "0.8",
    # }

    # pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer, options=pdf_options)
    # if pisa_status.err:
    #     return HttpResponse('PDF generation failed')
    
    # pdf_buffer.seek(0)
    email_from = "jomevictravels@quickwavetech.com"
    from_email = formataddr(("Jomevic Travels", email_from))
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=[recipient_email]
    )
    email.extra_headers = {"Reply-To": "jomevictravels@quickwavetech.com"}
    
    # Attach PDF
    # email.attach('report.pdf', pdf_buffer.getvalue(), 'application/pdf')
    
    # Optional: Add HTML email body
    # html_body = render_to_string('emails/email_itinerary_reserved.html', context)
    email.attach_alternative(html_string, "text/html")
    
    email.send()

    # Send email
    # send_mail(subject, plain_message, 'noreply@myreservationagent.com', [recipient_email], html_message=html_message)


def book_flight(request):
    if request.method == "POST":
        try:
            markups = None
            markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
            guest_office_id = request.POST.get('guest_office_id')
            flight = eval(request.POST.get('flight'))
            pay_small_small = request.POST.get('pay_small_small')
            flight_price_data = eval(request.POST.get('flight_price_data'))
            airline = eval(request.POST.get('airline_name'))
            flight_id = flight['id']
            # converter_data = convert_currency()
            traveller_data = create_flight_data(request)
            airlines = {}
            for data in flight_price_data['itineraries']:
                for segment in data['segments']:
                    airlines[segment['carrierCode']] = airline[segment['carrierCode']]
            contact = create_contact_information(request)
            amadeus_api = AmadeusAPI(guest_office_ids=guest_office_id)
            flight_data = amadeus_api.book_flight(traveller_data, flight_price_data, flight_id, contact)
            flight_details = amadeus_api.get_flight_data(flight_data['data']['id'])
            # user = CustomUser.objects.get(id=request.user.id)
            booking = Booking.objects.create(
                pnr=flight_data['data']['associatedRecords'][0]['reference'],
                amount=flight_price_data['price']['grandTotal'],
                office_id=guest_office_id,
                response=flight_details,
                init_response=flight_data,
                flight_data=flight,
                booking_id=flight_data['data']['id'],
                airlines=airlines,
                converted_amount="{:.2f}".format(
                    converter_data(guest_office_id) * float(flight_price_data['price']['grandTotal'])),
                farerules=amadeus_api.get_fare_rule(flight_price_data),
                seatmap=amadeus_api.get_seat_map(flight_data['data']['id'])
            )
            amount_to_add = 0.00
            if booking.response:
                amount_to_add = calculate_markup_fee_new(booking.response['data']['flightOffers'][0],
                                                             booking.office_id)
            # booking.converted_amount
            # Ensure the value being formatted is a valid float, not a tuple
            to_multiply = float(1.00)
            currencys = flight.get('price', {}).get('currency') or flight.get('price', {}).get('billingCurrency')
            if flight.get('converted_price') != flight['price']['grandTotal'] and currencys == "USD":
                to_multiply = float(get_currency_exchnage_rate(currencys))
                flight_data['is_converted'] = True

            booking.converted_amount = "{:.2f}".format(
                (float(converter_data(guest_office_id)) * (float(flight_price_data['price']['grandTotal']) + (amount_to_add))  * to_multiply)
            )
            booking.amount = booking.converted_amount
            booking.save()

            currency = booking.currency
            if booking.flight_data.get('is_converted'):
                currency = "NGN"
            # return redirect('bookinginfo', booking.id)
            url = request.build_absolute_uri(reverse('verify_payment'))
            paysmall = None
            if pay_small_small:
                paysmall = split_payments_with_dates(pay_small_small, float(booking.converted_amount), booking.booking_date)
                for pay in paysmall:
                    Pay_small_small.objects.create(
                        first_name=request.POST.get('booking_given_name_1'),
                        last_name=request.POST.get('booking_last_name_1'),
                        email=request.POST.get('booking_email_address_1'),
                        phone=request.POST.get('country_code_1') + " " + request.POST.get("booking_phone_number_1"),
                        amount=pay['amount'],
                        balance=pay['amount'],
                        due_date=pay['due_date'],
                        booking=booking,
                        payment_plan=pay_small_small,
                    )

            if request.POST.get("banks") == "paystack":
                paystack_amount = float(booking.converted_amount)
                paystack = Paystack()
                if pay_small_small:
                    booking.payment_type = "Pay In Bit"
                    first_pay = Pay_small_small.objects.filter(booking=booking, due_date=booking.booking_date).first()
                    paystack_amount = float(first_pay.amount)
                    payment_link = paystack.create_payment_link(
                        name="Payment for Services",
                        email=request.POST.get(f"booking_email_address_1"),
                        description=f"Payment for {booking}",
                        amount=paystack_amount * 100,
                        currency=currency,
                        redirect_url=url,
                        custom_fields=[
                            {"booking_id": f"{booking.booking_id}", "pnr": f"{booking.pnr}"}]
                    )
                    # booking.save()
                    # first_pay.paystack = payment_link
                    # first_pay.save()
                else:
                    paystack_amount = float(booking.converted_amount)
                    payment_link = paystack.create_payment_link(
                        name="Payment for Services",
                        email=request.POST.get(f"booking_email_address_1"),
                        description=f"Payment for {booking}",
                        amount=paystack_amount * 100,
                        currency=currency,
                        redirect_url=url,
                        custom_fields=[
                            {"booking_id": f"{booking.booking_id}", "pnr": f"{booking.pnr}"}]
                    )
                booking.save()
                # Generate a payment link
                if payment_link:
                    if isinstance(payment_link, str):
                        try:
                            import json
                            payment_link = json.loads(payment_link)  # Convert string to dictionary if necessary
                        except json.JSONDecodeError:
                            payment_link = {}  # Handle invalid JSON case

                    if isinstance(payment_link, dict) and payment_link.get('status'):
                        booking.payment_type = "Paystack"
                        booking.save()
                        paystack_url = payment_link['data'].get('authorization_url')
                        paystack_creation = PayStackTransaction.objects.create(
                            email=request.POST.get("booking_email_address_1"),
                            access_code=payment_link['data'].get('access_code'),
                            reference=payment_link['data'].get('reference'),
                            amount=float(booking.converted_amount),
                            booking=booking,
                            currency=currency,
                            payment_type="Paystack",
                        )

                        if paysmall:
                            first_pay.paystack = paystack_creation
                            first_pay.save()
                        return redirect(paystack_url)
                        
            elif request.POST.get("banks") == "flutter_wave":
                booking.payment_type = "Flutter Wave"
                email=request.POST.get(f"booking_email_address_1")
                phone_number=request.POST.get('country_code_1') + " " + request.POST.get("booking_phone_number_1")
                if pay_small_small:
                    booking.payment_type = "Pay In Bit"
                    first_pay = Pay_small_small.objects.filter(booking=booking, due_date=booking.booking_date).first()
                    flutter_amount = float(first_pay.amount)
                    booking.save()
                    return redirect(f'/transaction/flutter-payment/form/?amount={flutter_amount}&email={email}&phone_number={phone_number}&booking={booking.id}&first_pay={first_pay.id}')
                else:
                    booking.save()
                    return redirect(f'/transaction/flutter-payment/form/?amount={float(booking.converted_amount)}&email={email}&phone_number={phone_number}&booking={booking.id}')
            subject = "Jomivic Travels Placement"
            # from_email = 'jomevictravels@quickwavetech.com'
            from_email = formataddr(("Jomivic Travels", "jomevictravels@quickwavetech.com"))
            send_booking_email(request, booking.response, request.POST.get(f"booking_email_address_1"), booking)

            send_mail(
                subject,
                f"A Booking has been made on your platform Here's your The reference: {booking.formatted_id}",
                from_email,
                ["chinedue856@gmail.com"],
                # html_message=html_message,
                fail_silently=False,
            )
            return redirect('viewItinerary', booking.id)
        except Exception as e:
            print(e)
            messages.error(request, "Cannot Book flight, search or book another")
            return render(request, 'super/booking_failure.html')
            return redirect("dashboard")


def cancel_booking(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        try:
            amadeus_api = AmadeusAPI(guest_office_ids=booking.office_id)
            flight_data = amadeus_api.cancel_flight(booking.response["data"]["id"])
            if flight_data.status_code == 200 or flight_data.status_code == 204:
                booking.status = "Cancelled"
                booking.save()
            else:
                booking.status = "Voided"
                booking.save()

            return redirect('bookinginfo', booking_id)
        except Exception as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")


def update_booking_info(request, booking_id):
    if request.method == "POST":
        try:
            booking = get_object_or_404(Booking, id=booking_id)
            flight_id = booking.response['data']['id']
            if request.POST.get("update_type") == "passport":
                traveller_data = create_flight_data(request, booking)
            if request.POST.get("update_type") == "frequent_flyer":
                traveller_data = create_flight_data_1(request, booking)
            amadeus_api = AmadeusAPI(guest_office_ids=booking.office_id)
            flight_data = amadeus_api.update_flight_traveller_document(flight_id, traveller_data)
            if flight_data:
                user = CustomUser.objects.get(id=request.user.id)
                booking.response = flight_data
                # if user.private:
                #     booking.private_company = user.private
                # elif user.corporate_business:
                #     booking.corporate_company = user.corporate_business
                booking.save()
            return redirect('bookinginfo', booking_id)
        except Exception as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}")


def generate_pdf_from_html(html_content):
    pdf = pisa.CreatePDF(html_content)
    return pdf.dest.getvalue()


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def send_pdf_via_email(request, booking_id):
    if request.method == 'POST':
        # Get form data
        email_address = request.POST.get('email')
        email_with_receipt = request.POST.get('email_with_receipt')
        booking_db = request.POST.get('booking_db')
        booking = Booking.objects.get(id=booking_id)
        email_address = email_address.split(",")
        # Handle the PDF file if present
        if email_with_receipt.lower() == 'yes':
            email_template = "emails/email_itinerary_manage_receipt.html"
        else:
            email_template = "emails/email_itinerary_manage_no_receipt.html"
        send_email_booking_email(request, email_address, booking, email_template)

        return HttpResponse("Email sent successfully.")

    return HttpResponse("Invalid request.")




def update_booking(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        try:
            amadeus_api = AmadeusAPI(guest_office_ids=booking.office_id)
            new_flight_price = amadeus_api.flight_pricing(booking.flight_data)
            flight_data = amadeus_api.get_flight_data(booking.response["data"]["id"])
            if flight_data is None:
                flight_data = amadeus_api.get_flight_data_by_pnr(booking.pnr, booking.response['data']['flightOffers'][0]['source'])
                if flight_data and flight_data.get('data'):
                    booking.booking_id = flight_data['data']['id']
                else:
                    flight_data = None
            if flight_data:
                booking.response = flight_data
                if new_flight_price:
                    booking.new_flight_price = new_flight_price['data']['flightOffers'][0]
                    # farerules=amadeus_api.get_fare_rule(new_flight_price),
                    farerules=amadeus_api.get_fare_rule(new_flight_price['data']['flightOffers'][0])
                    booking.farerules = farerules

                for data in flight_data['data'].get('flightOffers', []):
                    for itinerary in data.get('itineraries', []):
                        for segment in itinerary.get('segments', []):
                            booking_status = segment.get("bookingStatus", "").upper()
                            if booking_status == "CANCELLED":
                                booking.status = "Cancelled"
                                # Note i added this line to turn the cancelled back to reserved if error remove this code.
                            else:
                                booking.status = "Reserved"


                # airlines = {}
                # for data in flight_data['data'].get('flightOffers', []):
                #     for segment in data.get('itineraries', []):
                #         for seg in segment.get('segments', []):
                #             carrier_code = seg.get('carrierCode')
                #             if carrier_code:
                #                 carrier_name = airlines.get(carrier_code, "Unknown Airline")
                #                 airlines[carrier_code] = carrier_name
                # booking.airlines = airlines
                if "tickets" in flight_data["data"]:
                    for ticket in flight_data["data"]["tickets"]:
                        document_status = ticket.get("documentStatus", "").upper()

                        if document_status == "ISSUED":
                            booking.status = "Issued"
                        elif document_status == "VOID":
                            booking.status = "Voided"
                        elif document_status == "REFUND":
                            booking.status = "Refunded"
                        elif document_status == "EXCHANGE":
                            booking.status = "Exchanged"
                else:
                    if booking.status != "Cancelled":
                        booking.status = "Reserved"
            else:
                booking.status = "Cancelled"


            booking.save()
            return redirect('bookinginfo', booking_id)

        except Exception as e:
            error_content = e.response.text if e.response else str(e)
            logging.error(
                f"Failed to Get Fare Rule: {e}\nError content: {error_content}"
            )
            return redirect('bookinginfo', booking_id)


def load_airlines(request):
    airlines = []
    csv_file_path = os.path.join(settings.BASE_DIR, 'ALL_Airlines_Form_New_Site.csv')

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            airline_name = row.get('Airline Name')
            airline_code = row.get('Airline Code')
            airlines.append({
                'name': airline_name,
                'code': airline_code
            })
    return JsonResponse({'airlines': airlines})
    # return airlines


def load_cities(request):
    cities = []
    csv_file_path = os.path.join(settings.BASE_DIR, 'all_data_amd.csv')

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            country_code = row.get('Country Code')
            city_code = row.get('City Code')
            country = row.get('Country')
            city_name = row.get('City Name')
            cities.append({
                'country_code': country_code,
                'city_code': city_code,
                'country': country,
                'city_name': city_name,
            })
    return JsonResponse({'cities': cities})
    # return airlines


def get_cities(request):
    countries = request.GET.getlist('countries')
    countries = [i.upper() for i in countries]
    # Query to get cities for the selected countries
    all_cities = City.objects.filter(country_code__in=countries)


    # Create a list of dictionaries containing city details
    cities_data = [{'city_code': city.city_code, 'city_name': city.city_name} for city in all_cities]

    # Return the cities as a JSON response
    return JsonResponse({'cities': cities_data})


def flight_search_v2(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)

    if request.method == "POST":
        markups = None
        markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        flight_data = None
        total_count = 0
        stop_counts = set()
        cabin_classes = set()
        min_price = None
        max_price = None
        office_ids_with_results = set()
        airlines = []
        baggage_options = []
        # Usage
        data = create_booking_json(request)
        # converter_data = convert_currency()
        amadeus_api = AmadeusAPI()
        result_dictionaries = {}
        travelers = data['travelers']
        originDestinations = data['originDestinations']
        travelClass = request.POST.get('flight_type')
        travel_type = request.POST.get('travel_type')
        origin_display = request.POST.get('origin_display')
        destination_display = request.POST.get('destination_display')
        flight_data = amadeus_api.search_flight(travelers=travelers, originDestinations=originDestinations,
                                                travelClass=travelClass)

        if flight_data:
            total_count = sum(len(result.get('data', [])) for result in flight_data.values())

            if total_count > 0:

                # Add is_oneway flag to flight data
                for flight_id, details in flight_data.items():

                    # For Office ID Filter
                    if 'data' in details and details['data']:
                        office_ids_with_results.add(flight_id)
                        # details['data'] = sorted(details['data'], key=lambda offer: float(offer['price']['grandTotal']))

                    for offer in details['data']:
                        itineraries = offer.get('itineraries', [])
                        amount_to_add = 0.00
                        if markups:
                            amount_to_add += calculate_company_markup(offer, markups, request.user)

                        amount_to_add = calculate_markup_fee_new(offer, flight_id)

                        offer['converted_price'] = "{:.2f}".format(
                            converter_data(flight_id) * (float(offer['price']['grandTotal']) + amount_to_add))
                        offer['is_oneway'] = len(itineraries) == 1
                        offer['is_multicity'] = len(itineraries) > 2

                        for itinerary in itineraries:
                            # Convert duration
                            itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])

                            # Fetch city name for the first segment's departure
                            first_segment = itinerary['segments'][0]
                            origin_code = first_segment['departure']['iataCode']
                            origin_city_name = get_city_name_by_airport_code(origin_code)

                            # Fetch city name for the last segment's arrival
                            last_segment = itinerary['segments'][-1]
                            destination_code = last_segment['arrival']['iataCode']
                            destination_city_name = get_city_name_by_airport_code(destination_code)

                            # Append city names to itinerary
                            itinerary['origin_city_name'] = origin_city_name
                            itinerary['destination_city_name'] = destination_city_name

                            # Calculate layover for multi-segment flights
                            segments = itinerary['segments']
                            for i in range(len(segments) - 1):
                                current_segment = segments[i]
                                next_segment = segments[i + 1]

                                # Calculate layover time between current segment and next segment
                                layover_hours, layover_minutes = calculate_layover_time(
                                    current_segment['arrival']['at'],
                                    next_segment['departure']['at']
                                )

                                # Store layover time in the current segment
                                current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                            # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                            segments[-1]['layover_time'] = None

                            # Process each segment
                            for segment in segments:
                                duration = segment.get('duration', None)
                                if duration:
                                    segment['readable_duration'] = convert_iso8601_duration(duration)
                                else:
                                    # Handle the case where 'duration' is missing
                                    segment['readable_duration'] = 'N/A'
                                departure_code = segment['departure']['iataCode']
                                arrival_code = segment['arrival']['iataCode']
                                segment['departure_city_name'] = get_city_name_by_airport_code(departure_code)
                                segment['arrival_city_name'] = get_city_name_by_airport_code(arrival_code)

                        # for Stops Filter
                        for itinerary in itineraries:
                            stop_counts.add(len(itinerary.get('segments', [])) - 1)

                        # For Cabin  Filter
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            cabin_classes.add(fareDetail.get('cabin', 'Economy'))

                        #  For Baggages Filter
                        baggage_options = set()
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            quantity = fareDetail.get('includedCheckedBags', {}).get('quantity', '0')
                                            numeric_quantity = extract_baggage_quantity(quantity)
                                            baggage_options.add(numeric_quantity)

                min_price, max_price = set_price_range(flight_data)

                airlines = set()
                # For Airlines Filter
                for flight_id, details in flight_data.items():
                    if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                        carriers = details['dictionaries']['carriers']
                        for offer in details['data']:
                            for itinerary in offer.get('itineraries', []):
                                for segment in itinerary.get('segments', []):
                                    carrier_code = segment.get('carrierCode')
                                    if carrier_code and carrier_code in carriers:
                                        airline_name = carriers[carrier_code]
                                        result_dictionaries[carrier_code] = airline_name
                                        airlines.add(airline_name)


        to_and_fro = get_to_and_fro(request)

    context = {
        # "user_permissions_codenames": user_permissions_codenames,
        # "flight_data": flight_data,
        "total_count": total_count,
        "airlines": sorted(airlines),
        "travelClass": travelClass,
        "travel_type": travel_type,
        "travelers": travelers,
        "origin_display": origin_display,
        "destination_display": destination_display,
        "stop_counts": sorted(stop_counts),
        "cabin_classes": list(cabin_classes),
        "baggage_options": list(map(int, baggage_options)),
        "data": request.POST,
        "post_data": json.dumps(dict(request.POST)),
        "to_and_fro": to_and_fro,
        'min_price': min_price,
        'max_price': max_price,
        'office_ids_with_results': office_ids_with_results,
        "user_permissions_codenames": list(user_permissions_codenames),
        "flight_data": json.dumps(flight_data),
    }

    return render(request, 'super/flight_results_2.html', context)


def group_flights_by_airline(flight_data):
    grouped_flights = defaultdict(list)

    for flight_id, details in flight_data.items():
        if 'data' in details:
            for offer in details['data']:
                offer['guest_office_id'] = flight_id
                offer['airline_dictionaries'] = details['dictionaries']
                itineraries = offer.get('itineraries', [])
                for itinerary in itineraries:
                    for segment in itinerary.get('segments', []):
                        carrier_code = segment.get('carrierCode')
                        if carrier_code:
                            # Assuming the carrier name is available in 'dictionaries' under 'carriers'
                            airline_name = details['dictionaries']['carriers'].get(carrier_code)
                            if airline_name:
                                grouped_flights[airline_name].append(offer)

    return grouped_flights


@login_required(login_url='signin')
def flight_search_v3(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)

    if request.method == "POST":
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = False
        # Check if the request comes from a mobile device
        if 'Mobi' in user_agent or 'Android' in user_agent:
            is_mobile = True
        markups = None
        markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
        flight_data = None
        total_count = 0
        grouped_flights = None
        stop_counts = set()
        cabin_classes = set()
        min_price = None
        max_price = None
        office_ids_with_results = set()
        airlines = []
        baggage_options = []
        # Usage
        data = create_booking_json(request)
        # converter_data = convert_currency()
        amadeus_api = AmadeusAPI()
        result_dictionaries = {}
        travelers = data['travelers']
        originDestinations = data['originDestinations']
        travelClass = request.POST.get('flight_type')
        travel_type = request.POST.get('travel_type')
        origin_display = request.POST.get('origin_display')
        destination_display = request.POST.get('destination_display')
        flight_data = amadeus_api.search_flight(travelers=travelers, originDestinations=originDestinations,
                                                travelClass=travelClass, phone_search=is_mobile)


        if flight_data:
            total_count = sum(len(result.get('data', [])) for result in flight_data.values())

            if total_count > 0:

                # Add is_oneway flag to flight data
                for flight_id, details in flight_data.items():

                    # For Office ID Filter
                    if 'data' in details and details['data']:
                        office_ids_with_results.add(flight_id)
                        # details['data'] = sorted(details['data'], key=lambda offer: float(offer['price']['grandTotal']))

                    for offer in details['data']:
                        itineraries = offer.get('itineraries', [])
                        amount_to_add = 0.00
                        amount_to_add_2 = 0.00
                        if markups:
                            amount_to_add_2 += calculate_company_markup(offer, markups, request.user)

                        amount_to_add = calculate_markup_fee_new(offer, flight_id)

                        offer['converted_price'] = "{:.2f}".format(converter_data(flight_id) * (float(offer['price']['grandTotal']) + amount_to_add) + amount_to_add_2)
                        offer['is_oneway'] = len(itineraries) == 1
                        offer['is_multicity'] = len(itineraries) > 2

                        for itinerary in itineraries:
                            # Convert duration
                            itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])

                            # Fetch city name for the first segment's departure
                            first_segment = itinerary['segments'][0]
                            origin_code = first_segment['departure']['iataCode']
                            origin_city_name = get_city_name_by_airport_code(origin_code)

                            # Fetch city name for the last segment's arrival
                            last_segment = itinerary['segments'][-1]
                            destination_code = last_segment['arrival']['iataCode']
                            destination_city_name = get_city_name_by_airport_code(destination_code)

                            # Append city names to itinerary
                            itinerary['origin_city_name'] = origin_city_name
                            itinerary['destination_city_name'] = destination_city_name

                            # Calculate layover for multi-segment flights
                            segments = itinerary['segments']
                            for i in range(len(segments) - 1):
                                current_segment = segments[i]
                                next_segment = segments[i + 1]

                                # Calculate layover time between current segment and next segment
                                layover_hours, layover_minutes = calculate_layover_time(
                                    current_segment['arrival']['at'],
                                    next_segment['departure']['at']
                                )

                                # Store layover time in the current segment
                                current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                            # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                            segments[-1]['layover_time'] = None


                            # Process each segment
                            for segment in segments:
                                duration = segment.get('duration', None)
                                if duration:
                                    segment['readable_duration'] = convert_iso8601_duration(duration)
                                else:
                                    # Handle the case where 'duration' is missing
                                    segment['readable_duration'] = 'N/A'
                                departure_code = segment['departure']['iataCode']
                                arrival_code = segment['arrival']['iataCode']
                                segment['departure_city_name'] = get_city_name_by_airport_code(departure_code)
                                segment['arrival_city_name'] = get_city_name_by_airport_code(arrival_code)

                        # for Stops Filter
                        for itinerary in itineraries:
                            stop_counts.add(len(itinerary.get('segments', [])) - 1)

                        # For Cabin  Filter
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            cabin_classes.add(fareDetail.get('cabin', 'Economy'))

                        #  For Baggages Filter
                        baggage_options = set()
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            quantity = fareDetail.get('includedCheckedBags', {}).get('quantity', '0')
                                            numeric_quantity = extract_baggage_quantity(quantity)
                                            baggage_options.add(numeric_quantity)

                min_price, max_price = set_price_range(flight_data)
                dictionaries_airlines = {}
                airlines = set()
                # For Airlines Filter
                for flight_id, details in flight_data.items():
                    if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                        carriers = details['dictionaries']['carriers']
                        for offer in details['data']:
                            for itinerary in offer.get('itineraries', []):
                                for segment in itinerary.get('segments', []):
                                    carrier_code = segment.get('carrierCode')
                                    if carrier_code and carrier_code in carriers:
                                        airline_name = carriers[carrier_code]
                                        result_dictionaries[carrier_code] = airline_name
                                        airlines.add(airline_name)


                # for flight_id, details in flight_data.items():
                #     if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                #         # Get the carriers directly from the dictionaries
                #         carriers = details['dictionaries']['carriers']
                #         # Add each airline name to the airlines set
                #         for airline_name in carriers.values():
                #             airlines.add(airline_name)

                grouped_flights = group_flights_by_airline(flight_data)
                airlines = sorted(grouped_flights.keys())
                # GROUPED_FLIGHTS = {}
                # for key,value in grouped_flights.items():
                #     GROUPED_FLIGHTS[key] = value

        to_and_fro = get_to_and_fro(request)

    context = {
        "user_permissions_codenames": user_permissions_codenames,
        "flight_data": flight_data,
        "total_count": total_count,
        "grouped_flights": dict(grouped_flights),
        "airlines": sorted(airlines),
        "travelClass": travelClass,
        "travel_type": travel_type,
        "travelers": travelers,
        "origin_display": origin_display,
        "destination_display": destination_display,
        "stop_counts": sorted(stop_counts),
        "cabin_classes": list(cabin_classes),
        "baggage_options": list(map(int, baggage_options)),
        "data": request.POST,
        "post_data": json.dumps(dict(request.POST)),
        "to_and_fro": to_and_fro,
        'min_price': min_price,
        'max_price': max_price,
        'office_ids_with_results': office_ids_with_results,
        'result_dictionaries': result_dictionaries,
    }

    return render(request, 'super/flight_results_2.html', context)


def parse_flight_data(flight_data):
    """
    Parse and process the flight data string into a dictionary.
    Returns the processed dictionary or None if parsing fails.
    """
    try:
        # Decode and clean up the string if necessary
        decoded_string = str(flight_data)

        return decoded_string
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print("Error processing flight data:", str(e))
        return None


def format_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%b %d, %Y"), dt.strftime("%I:%M %p")


def get_upsell(request):
    if request.method == "POST":
        try:
            markups_tykkt = MarkupRuleTyktt.objects.filter(is_active=True)
            data = json.loads(request.body)
            upsell_offers = {}
            # converter_data = convert_currency()

            flight_data = eval(data.get('flight'))
            itineraries = flight_data.get('itineraries', [])
            is_converted =  False
            to_multiply = 1.00
            currencys = flight_data.get('price', {}).get('currency') or flight_data.get('price', {}).get('billingCurrency')
            if flight_data.get('converted_price') != flight_data['price']['grandTotal'] and currencys == "USD":
                to_multiply = float(get_currency_exchnage_rate(currencys))
                flight_data['is_converted'] = True # Mark the flight data as converted
                is_converted = True
            results = []

            for itinerary in itineraries:  # Iterate over each itinerary
                segments = itinerary.get("segments", [])  # Access the 'segments' key
                first_segment = segments[0]

                last_segment = segments[-1]
                departure_date, departure_time = format_datetime(first_segment["departure"]["at"])
                arrival_date, arrival_time = format_datetime(last_segment["arrival"]["at"])
                results.append({
                    # "traffic": "Departure",
                    "departure_airport": first_segment['departure']['iataCode'],
                    "departure_airline": first_segment['carrierCode'],
                    "departure_date": departure_date,
                    "departure_time": departure_time,
                    # "traffic": "Arrival",
                    "arrival_airport": last_segment['arrival']['iataCode'],
                    "arrival_airline": last_segment['carrierCode'],
                    "arrival_date": arrival_date,
                    "arrival_time": arrival_time
                })

            office_id = data.get('officeid')
            amadues_api = AmadeusAPI(guest_office_ids=office_id)
            up_sell = amadues_api.get_upsell(flight_data)
            if up_sell:
                if up_sell.get('meta', {}).get('count', 0) > 0:
                    for index, offer in enumerate(up_sell.get('data', [])):
                        # amount_to_add = 0.00
                        amount_to_add = calculate_markup_fee_new(offer, office_id)
                        # offer['converted_price'] = "{:.2f}".format(converter_data[office_id] * (
                        #             float(offer['price']['grandTotal']) + amount_to_add))
                        # upsell_offers['converted_price'] = offer['converted_price']
                        # if offer['id'] not in upsell_offers:
                        offer['converted_price'] = "{:.2f}".format((converter_data(office_id) * (float(offer['price']['grandTotal']) + amount_to_add)) * to_multiply)
                        flight_data['is_converted'] = is_converted
                        upsell_offers[offer['id']] = {
                            "Baggage": {},
                            "Flexibility": {},
                            "Meal & More": {},
                            "flight": offer,
                            "converted_price": offer['converted_price']

                        }
                        itineraries = offer.get('itineraries', [])

                        for itinerary in itineraries:
                            # Convert duration
                            # itinerary['readable_duration'] = convert_iso8601_duration(itinerary['duration'])
                            # Fetch city name for the first segment's departure
                            first_segment = itinerary['segments'][0]
                            origin_code = first_segment['departure']['iataCode']
                            origin_city_name = get_city_name_by_airport_code(origin_code)

                            # Fetch city name for the last segment's arrival
                            last_segment = itinerary['segments'][-1]
                            destination_code = last_segment['arrival']['iataCode']
                            destination_city_name = get_city_name_by_airport_code(destination_code)

                            # Append city names to itinerary
                            itinerary['origin_city_name'] = origin_city_name
                            itinerary['destination_city_name'] = destination_city_name

                            # Calculate layover for multi-segment flights
                            segments = itinerary['segments']
                            for i in range(len(segments) - 1):
                                current_segment = segments[i]
                                next_segment = segments[i + 1]

                                # Calculate layover time between current segment and next segment
                                layover_hours, layover_minutes = calculate_layover_time(
                                    current_segment['arrival']['at'],
                                    next_segment['departure']['at']
                                )

                                # Store layover time in the current segment
                                current_segment['layover_time'] = f"{int(layover_hours)}h {int(layover_minutes // 60)}m"

                            # Ensure the last segment doesn't have a layover (since it's the end of the journey)
                            segments[-1]['layover_time'] = None

                            # Process each segment
                            for segment in segments:
                                duration = segment.get('duration', None)
                                if duration:
                                    segment['readable_duration'] = convert_iso8601_duration(duration)
                                else:
                                    # Handle the case where 'duration' is missing
                                    segment['readable_duration'] = 'N/A'
                                departure_code = segment['departure']['iataCode']
                                arrival_code = segment['arrival']['iataCode']
                                segment['departure_city_name'] = get_city_name_by_airport_code(departure_code)
                                segment['arrival_city_name'] = get_city_name_by_airport_code(arrival_code)

                        # for Stops Filter

                        #  For Baggages Filter
                        baggage_options = set()
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                for traveler in offer['travelerPricings']:
                                    for fareDetail in traveler['fareDetailsBySegment']:
                                        if fareDetail['segmentId'] == segment['id']:
                                            quantity = fareDetail.get('includedCheckedBags', {}).get('quantity', '0')
                                            numeric_quantity = extract_baggage_quantity(quantity)
                                            baggage_options.add(numeric_quantity)
                        # add flight data

                        for travelers_pricing in offer.get('travelerPricings', []):
                            for data in travelers_pricing.get('fareDetailsBySegment', []):
                                for fare_rule in data.get('amenities', []):
                                    amenity_type = fare_rule.get('amenityType')
                                    description = fare_rule.get('description', "Information not available")

                                    offer_id = offer['id']
                                    if offer_id not in upsell_offers:
                                        upsell_offers[offer_id] = {
                                            'Baggage': {},
                                            'Flexibility': {},
                                            'Meal & More': {}
                                        }

                                    # Handle baggage amenities
                                    if amenity_type == "BAGGAGE":
                                        upsell_offers[offer_id]['Baggage'].setdefault(description, 0)
                                        upsell_offers[offer_id]['Baggage'][description] += 1

                                    # Handle flexibility information
                                    elif amenity_type == "BRANDED_FARES":
                                        upsell_offers[offer_id]['Flexibility'].setdefault(description, 0)
                                        upsell_offers[offer_id]['Flexibility'][description] += 1

                                    # Handle meal and entertainment amenities
                                    elif amenity_type in ["MEAL", "ENTERTAINMENT"]:
                                        upsell_offers[offer_id]['Meal & More'].setdefault(description, 0)
                                        upsell_offers[offer_id]['Meal & More'][description] += 1

            if not flight_data:
                return JsonResponse({"error": "Missing 'flight' data"}, status=400)
            upsell_response = JsonResponse({"up_sell": upsell_offers, "count": up_sell['meta']['count'], "results": results})
            return upsell_response
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", str(e))
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

