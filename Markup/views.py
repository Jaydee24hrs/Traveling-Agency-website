import json
import re

from django.http import JsonResponse

from Booking.flightbooking import AmadeusAPI
from Booking.utils import calculate_markup_fee_new
from Booking.views import calculate_layover_time
from Booking.views import convert_currency, create_booking_json, convert_iso8601_duration, \
    get_city_name_by_airport_code, extract_baggage_quantity, set_price_range, get_to_and_fro
from User.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .forms import ExchangeRateExclutionForm, ExchangeRateForm, MarkupRuleTykttForm, TykttMarkUpForm
from .models import ExchangeRate, ExchangeRateExclution, MarkupRuleTyktt, TykttMarkUp, TykttMarkupCommission


office_ids = ['LOSN828HJ']


all_markup_rules_fields = ['apply_markup_at', 'fare_type', 'passenger_type', 'marketing_carrier',
                           'operating_carrier', 'air_providers'
                                                'validating_carrier', 'affiliate_carrier', 'fare_basis_code',
                           'journey_type',
                           'cabin_classes', 'office_id', 'cabin_classes'
                                                         'booking_class_of_service', 'from_country', 'from_city',
                           'to_country', 'to_city',
                           'exclude_marketing_carrier',
                           'exclude_operating_carrier', 'exclude_validating_carrier', 'exclude_affiliate_carrier',
                           'exclude_booking_classes', 'exclude_fare_basis_code',
                           'exclude_from_country', 'exclude_from_city', 'exclude_to_country', 'exclude_to_city']


# CRUD for MarkupRuleTyktt
def markup_rule_tyktt_list(request):
    markup_rules = MarkupRuleTyktt.objects.all()
    return render(request, 'markup_rule_tyktt_list.html', {'markup_rules': markup_rules})


@login_required(login_url='signin')
def markup_rule_tyktt_create(request):
    if request.method == 'POST':
        form = MarkupRuleTykttForm(request.POST)
        print(form.errors)
        messages.error(request, form.errors)
        if form.is_valid():
            # Save the form with commit=False so we can handle the fields manually
            markup_manager = form.save(commit=False)
            markup_manager.is_active = True

            # Iterate through the multi-choice fields and convert list values to a comma-separated string
            for field in all_markup_rules_fields:
                if request.POST.getlist(field):
                    setattr(markup_manager, field, ','.join(request.POST.getlist(field)))
                else:
                    setattr(markup_manager, field, '')  # Set empty string if no choice selected

            # Save the model instance after handling all fields
            markup_manager.save()
            messages.success(request, "Markup rule created successfully")

            return redirect('markup')
    else:
        form = MarkupRuleTykttForm()

    return render(request, 'super/markup.html', {'form': form})


@login_required(login_url='signin')
def markup_rule_tyktt_update(request, pk):
    markup_rule = get_object_or_404(MarkupRuleTyktt, pk=pk)
    if request.method == 'POST':
        form = MarkupRuleTykttForm(request.POST, instance=markup_rule)
        if form.is_valid():
            markup_manager = form.save(commit=False)

            for field in all_markup_rules_fields:
                new_value = request.POST.getlist(field)  # Get the value from the form request

                # Only update if the new value is provided and not empty, otherwise keep the original
                if new_value:
                    setattr(markup_manager, field, ','.join(new_value))
                else:
                    # Keep the original value from the model if no new value is provided
                    original_value = getattr(markup_manager, field)
                    setattr(markup_manager, field, original_value)

            markup_manager.save()
            messages.success(request, "Markup rule updated successfully")
            return redirect('markup')
        else:
            messages.error(request, form.errors)

    return redirect('markup')


@login_required(login_url='signin')
def markup_rule_tyktt_delete(request, pk):
    markup_rule = get_object_or_404(MarkupRuleTyktt, pk=pk)
    if request.method == 'POST':
        markup_rule.delete()
        messages.success(request, "Markup rule deleted successfully")
        return redirect('markup')
    return redirect('markup')


@login_required(login_url='signin')
def update_markup_rule(request, pk):
    markup_rule = get_object_or_404(MarkupRuleTyktt, pk=pk)

    if request.method == 'POST':
        # Toggle the is_active status
        markup_rule.is_active = not markup_rule.is_active
        markup_rule.save()  # Save the changes to the database

        messages.success(request, "Markup rule updated successfully")

    return redirect('markup')


def converter_data(office_id):
    exchange_rate = ExchangeRate.objects.filter(office_id=office_id).first()
    if exchange_rate:
        return exchange_rate.rate
    return 1.0


@login_required(login_url='signin')
def flight_search_markup(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)

    if request.method == "POST":
        markups = None
        markups_tykkt = MarkupRuleTyktt.objects.all()
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
        travelers = data['travelers']
        originDestinations = data['originDestinations']
        travelClass = request.POST.get('flight_type')
        travel_type = request.POST.get('travel_type')
        origin_display = request.POST.get('origin_display')
        destination_display = request.POST.get('destination_display')
        flight_data = amadeus_api.search_flight(travelers=travelers, originDestinations=originDestinations,
                                                travelClass=travelClass)

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

                    for offer in details['data']:
                        itineraries = offer.get('itineraries', [])
                        amount_to_add = 0.00
                        amount_to_add = calculate_markup_fee_new(offer, flight_id)

                        offer['converted_price'] = "{:.2f}".format(
                            converter_data(flight_id) * (float(offer['price']['grandTotal']) + amount_to_add))
                        # print(markups)
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
                                        airlines.add(airline_name)

                # for flight_id, details in flight_data.items():
                #     if 'dictionaries' in details and 'carriers' in details['dictionaries']:
                #         # Get the carriers directly from the dictionaries
                #         carriers = details['dictionaries']['carriers']
                #         # Add each airline name to the airlines set
                #         for airline_name in carriers.values():
                #             airlines.add(airline_name)

        to_and_fro = get_to_and_fro(request)

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
    }

    return render(request, 'super/flight_markup_results.html', context)


@login_required(login_url='signin')
def duplicate_markup_rule(request, pk):
    # Fetch the original record
    original_record = get_object_or_404(MarkupRuleTyktt, pk=pk)

    # Create a new record by copying the original record
    original_record.pk = None
    original_record.is_active = False 
    original_record.name = f"Copy of {original_record.name}"

    # Save the new duplicated record
    original_record.save()

    # Redirect to a page (you can choose a different redirect target)
    return redirect('markup')


# Create View
@login_required(login_url="signin")
def markup_create(request):
    if request.method == "POST":
        markup_form = TykttMarkUpForm(request.POST)
        if markup_form.is_valid():
            markup = markup_form.save(commit=False)
            checked_items = [key for key in office_ids if request.POST.get(key) == 'on']
            # Join them as a comma-separated string
            checked_items_str = ','.join(checked_items)
            markup.office_id = checked_items_str
            markup.corporate_code = ','.join(request.POST.getlist('corporate_code_input'))
            markup.save()
            currency_list = request.POST.getlist('currency')
            to_add = len(request.POST.getlist('amount')) - len(request.POST.getlist('currency'))
            if to_add > 0:
                currency_list = [''] * to_add + currency_list
            fare_types = request.POST.getlist('fare_type')
            to_add = len(request.POST.getlist('amount')) - len(request.POST.getlist('fare_type'))
            if to_add > 0:
                fare_types = [''] * to_add + fare_types

            for index, amount in enumerate(request.POST.getlist("amount")):
                if amount:
                    TykttMarkupCommission.objects.create(
                        markup_commission=request.POST.getlist("markup_commission")[
                            index
                        ],
                        departure_type=request.POST.getlist("departure_type")[index],
                        departure=request.POST.getlist("departure")[index],
                        arrival_type=request.POST.getlist("arrival_type")[index],
                        arrival=request.POST.getlist("arrival")[index],
                        operating_carrier=request.POST.getlist("operating_carrier")[
                            index
                        ],
                        carbin_class=request.POST.getlist("carbin_class")[index],
                        passenger=request.POST.getlist("passenger")[index],
                        office_id=request.POST.getlist("office_ids")[index],
                        currency=currency_list[index],
                        fare_type=fare_types[index],
                        validating_carrier=request.POST.getlist("validating_carrier")[
                            index
                        ],
                        amount=request.POST.getlist("amount")[index],
                        amount_type=request.POST.getlist("amount_type")[index],
                        markup=markup,
                    )
            messages.success(request, "Markup rule created successfully")
            return redirect("markup")
        else:
            messages.error(request, "Failed to create Markup")
    return redirect("markup")


# Update View
@login_required(login_url="signin")
def markup_update(request, pk):
    markup = get_object_or_404(TykttMarkUp, pk=pk)

    if request.method == 'POST':
        if markup:
            markup.is_marketing_carrier = request.POST.get('is_marketing_carrier') == 'on'
            markup.marketing_carrier = request.POST.get('marketing_carrier', '')
            markup.is_others = request.POST.get('is_others') == 'on'

            checked_items = [key for key in office_ids if request.POST.get(key) == 'on']
            corporate_codes = request.POST.getlist('corporate_code_input')
            if markup.corporate_code and corporate_codes:
                markup.corporate_code = ','.join(corporate_codes) + "," + markup.corporate_code
            elif corporate_codes:  # Check if the list is not empty
                markup.corporate_code = ','.join(corporate_codes)
                # markup.corporate_code = markup.corporate_code.rstrip(',')

            checked_items_str = ','.join(checked_items)
            markup.office_id = checked_items_str
            markup.save()
            currency_list = request.POST.getlist('currency')
            to_add = len(request.POST.getlist('amount')) - len(request.POST.getlist('currency'))
            if to_add > 0:
                currency_list = [''] * to_add + currency_list
            fare_types = request.POST.getlist('fare_type')
            to_add = len(request.POST.getlist('amount')) - len(request.POST.getlist('fare_type'))
            if to_add > 0:
                fare_types = [''] * to_add + fare_types
            for index, amount in enumerate(request.POST.getlist('amount')):
                if amount:
                    TykttMarkupCommission.objects.create(
                        markup_commission=request.POST.getlist('markup_commission')[index],
                        departure_type=request.POST.getlist('departure_type')[index],
                        departure=request.POST.getlist('departure')[index],
                        arrival_type=request.POST.getlist('arrival_type')[index],
                        arrival=request.POST.getlist('arrival')[index],
                        operating_carrier=request.POST.getlist('operating_carrier')[index],
                        carbin_class=request.POST.getlist('carbin_class')[index],
                        passenger=request.POST.getlist('passenger')[index],
                        fare_type=fare_types[index],
                        office_id=request.POST.getlist('office_ids')[index],
                        currency=currency_list[index],
                        validating_carrier=request.POST.getlist('validating_carrier')[index],
                        amount=request.POST.getlist('amount')[index],
                        amount_type=request.POST.getlist('amount_type')[index],
                        markup=markup
                    )
            messages.success(request, "Markup rule updated successfully")
            return redirect('markup')
    else:
        return redirect('markup')


@login_required(login_url='signin')
def markup_delete(request, pk):
    markup = get_object_or_404(TykttMarkUp, pk=pk)
    markup.delete()
    messages.success(request, "Markup rule deleted successfully")
    return redirect('markup')


@login_required(login_url='signin')
def markup_commission_delete(request, pk):
    markup = get_object_or_404(TykttMarkupCommission, pk=pk)
    markup.delete()
    messages.success(request, "Markup/Commission rule deleted successfully")
    return redirect('markup')


@login_required(login_url='signin')
def update_tyktt_markup_rule(request, pk):
    markup_rule = get_object_or_404(TykttMarkUp, pk=pk)

    if request.method == 'POST':
        # Toggle the is_active status
        markup_rule.is_active = not markup_rule.is_active
        markup_rule.save()  # Save the changes to the database

        messages.success(request, "Markup rule updated successfully")

    return redirect('markup')


# Exchange Rate
def exchange_rate_update_status(request, pk):
    rate = get_object_or_404(ExchangeRate, pk=pk)
    rate.status = not rate.status
    rate.save()
    messages.success(request, "Exchnage Rate Updated Successfully")
    return redirect('markup')

def exchange_rate_create(request):
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exchnage Rate Updated Successfully")
            return redirect('markup')
    else:
        messages.error(request, form.errors)
        form = ExchangeRateForm()
    return redirect('markup')

def exchange_rate_update(request, pk):
    rate = get_object_or_404(ExchangeRate, pk=pk)
    rate_status = rate.status
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST, instance=rate)
        if form.is_valid():
            rat = form.save(commit=False)
            rat.status = rate_status
            rat.save()
            messages.success(request, "Exchnage Rate Updated Successfully")
            return redirect('markup')
    else:
        form = ExchangeRateForm(instance=rate)
    return redirect('markup')

def exchange_rate_delete(request, pk):
    rate = get_object_or_404(ExchangeRate, pk=pk)
    if request.method == 'POST':
        rate.delete()
        messages.success(request, "Exchange rate Deleted Successfully")
        return redirect('markup')
    return redirect('markup')

# Similar views for ExchangeRateExclution
def exchange_rate_exclution_update_status(request, pk):
    exclution = get_object_or_404(ExchangeRateExclution, pk=pk)
    exclution.status = not exclution.status
    exclution.save()
    messages.success(request, "Exchnage Rate Exclution Updated Successfully")
    return redirect('markup')

def exchange_rate_exclution_create(request):
    if request.method == 'POST':
        form = ExchangeRateExclutionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exchnage Rate Created Successfully")
            return redirect('markup')
    else:
        form = ExchangeRateExclutionForm()
        messages.success(request, "Exchnage Rate Created Successfully")
    return redirect('markup')

def exchange_rate_exclution_update(request, pk):
    exclution = get_object_or_404(ExchangeRateExclution, pk=pk)
    if request.method == 'POST':
        form = ExchangeRateExclutionForm(request.POST, instance=exclution)
        if form.is_valid():
            form.save()
            messages.success(request, "Exchnage Exclude Rate Updated Successfully")
            return redirect('markup')
    else:
        form = ExchangeRateExclutionForm(instance=exclution)
        messages.error(request, "Exchnage Rate Exclusion Not Updated Successfully")
    return redirect('markup')

def exchange_rate_exclution_delete(request, pk):
    exclution = get_object_or_404(ExchangeRateExclution, pk=pk)
    if request.method == 'POST':
        exclution.delete()
        messages.success(request, "Exchnage Rate Exclusion Deleted Successfully")
        return redirect('markup')
    messages.error(request, "Exchnage Rate Exclusion Not Deleted Successfully")
    return redirect('markup')


def markup_delete_corporatecode(request):
    if request.method == "POST":
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            md_value = data.get("md")
            markup_id = data.get("markup_id")
            markup = get_object_or_404(TykttMarkUp, pk=markup_id)
            # Step 1: Replace the first occurrence of md_value
            markup.corporate_code = markup.corporate_code.replace(md_value, "", 1)

            # Step 2: Remove any leading, trailing, or duplicate commas
            markup.corporate_code = re.sub(r",\s*,+", ",", markup.corporate_code)  # Remove consecutive commas
            markup.corporate_code = re.sub(r"^,|,$", "", markup.corporate_code)  # Remove leading and trailing commas

            # Step 3: Convert to a list, ensuring no empty strings remain
            markup_list = [item.strip() for item in markup.corporate_code.split(",") if item.strip()]

            # Step 4: (Optional) Convert back to a cleaned string
            markup.corporate_code = ",".join(markup_list)
            markup.save()
            return JsonResponse({"success": True})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
