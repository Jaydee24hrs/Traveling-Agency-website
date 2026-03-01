
from datetime import datetime
from email.utils import formataddr
import hashlib
import hmac
import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict
from uuid import uuid4
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.http import (HttpRequest, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from dotenv import load_dotenv

from Booking.models import Booking
from Transaction.paystack import Paystack
from Transaction.paystack_integration import Paystack
from User.models import CustomUser

from .forms import FlutterPaymentForm, PaySmallSmallForm, TransactionForm
from .models import (FlutterwaveTransaction, ManualPayment, Pay_small_small,
                     PayStackTransaction, Transaction)
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_booking_email_2(response_data, recipient_email, booking):
    """
    Sends booking details extracted from the response data as an email with pink and blue styling using inline styles.
    
    Parameters:
    - response_data (dict): The booking data containing flight offers, travelers, etc.
    - recipient_email (str): The email address to send the booking information to.
    - booking (object): The booking object, which might include formatted ID or other details.
    """

    # Extract flight offers and travelers
    flight_offers = response_data.get("data", {}).get("flightOffers", [])
    travelers = response_data.get("data", {}).get("travelers", [])

    currency = booking.currency
    if booking.flight_data.get('is_converted'):
        currency = "NGN"

    # Construct subject and initial messages
    subject = f"Thank you for booking with us! Your reservation has been successfully placed. Here’s your booking reference: {booking.formatted_id}."
    plain_message = f"Thank you for booking with us! Your reservation has been successfully placed. Here’s your booking reference: {booking.formatted_id}.\n\n"

    # Styling for the HTML email with inline CSS for email compatibility
    html_message = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f1f9; padding: 20px;">
        <h2 style="color: #ff69b4;">Booking Confirmation for Trip ID: {}</h2>
        <p>Thank you for booking with us!, Booking informations are stated below</p>
    """.format(booking.formatted_id)

    # Add traveler information to plain message and HTML
    plain_message += "Traveler Information:\n"
    html_message += "<h3 style='color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px;'>Traveler Information:</h3>"
    for traveler in travelers:
        traveler_name = traveler["name"]["firstName"] + " " + traveler["name"]["lastName"]
        traveler_email = traveler["contact"]["emailAddress"]
        plain_message += f" - {traveler_name}, Email: {traveler_email}\n"
        html_message += f"<p style='margin: 5px 0;'><strong>{traveler_name}</strong>, Email: {traveler_email}</p>"
    plain_message += "\n"
    html_message += "<div style='padding: 10px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);'></div>"

    # Add flight itinerary information to plain message and HTML
    plain_message += "Flight Itineraries:\n"
    html_message += "<h3 style='color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px;'>Flight Itineraries:</h3>"
    for offer in flight_offers:
        itineraries = offer.get("itineraries", [])
        total_price = offer.get("price", {}).get("total", "N/A")

        for itinerary in itineraries:
            for segment in itinerary.get("segments", []):
                departure_airport = segment["departure"]["iataCode"]
                arrival_airport = segment["arrival"]["iataCode"]
                departure_date = datetime.fromisoformat(segment["departure"]["at"]).strftime('%Y-%m-%d %H:%M:%S')
                flight_number = segment["carrierCode"] + segment["number"]

                # Add details to plain message
                plain_message += (
                    f" - Flight {flight_number} from {departure_airport} to {arrival_airport} "
                    f"on {departure_date}\n"
                )

                # Add details to HTML message with inline styles
                html_message += f"""
                    <div style='padding: 10px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); margin-bottom: 20px;'>
                        <p style='margin: 5px 0;'><strong>Flight {flight_number}</strong> from {departure_airport} to {arrival_airport}</p>
                        <p style='margin: 5px 0;'>Departure: {departure_date}</p>
                    </div>
                """
        html_message += "<hr>"
        html_message += f"<p><strong>Total Price: {currency}  {float(total_price):,.2f}</strong></p>"
    html_message += "<div style='padding-top: 20px;'></div>"

    # Add footer and closing message to the HTML
    html_message += """
        <div style="font-size: 14px; color: #888; text-align: center; padding-top: 20px;">
            <p>For any assistance, feel free to contact us at <strong>Info@jomivictravels.com</strong></p>
            <p><a href="mailto:Info@jomivictravels.com" style="background-color: #ff69b4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Contact Us</a></p>
        </div>
    </body>
    </html>
    """

    # Footer text for plain message
    plain_message += "\nThank you for booking with Soft Crown Travels!"

    # Send the email
    # from_email = 'jomivictravels@quickwavetech.com'
    from_email = formataddr(("Jomivic Travels", "jomivictravels@quickwavetech.com"))
    recipient_list = [recipient_email]

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )


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


logger = logging.getLogger(__name__)
@login_required(login_url='signin')
def update_transaction(request, transaction_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if 'tyktt_create_transactions' in user_permissions_codenames or request.user.is_superuser:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if request.method == 'POST':
            form = TransactionForm(request.POST, instance=transaction)
            print(form.errors)
            if form.is_valid():
                trac = form.save(commit=False)
                user = CustomUser.objects.get(id=request.POST.get("agency"))
                if transaction.private_agency:
                    trac.private_agency = transaction.private_agency
                elif transaction.corporate_agency:
                    trac.corporate_agency = transaction.corporate_agency
                trac.save()
                return redirect('transactions')
            return redirect('transactions')
        else:
            return redirect('transactions')
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('transactions')


@login_required(login_url='signin')
def transactions(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    users = None
    if request.user.user_type == "tyktt" or request.user.is_superuser:
        users = CustomUser.objects.filter(is_owner=True).order_by('-id')
    elif request.user.user_type == "affiliate":
        user_id = request.user.id
        if request.user.private:
            users = CustomUser.objects.filter(id=user_id).order_by('-id')
        elif request.user.corporate_business:
            users = CustomUser.objects.filter(id=user_id).order_by('-id')

    transactions = None
    if request.user.user_type == "tyktt" or request.user.is_superuser:
        transactions = Transaction.objects.all().order_by('-id')
    elif request.user.user_type == "affiliate":
        if request.user.private:
            transactions = Transaction.objects.filter(private_agency=request.user.private.id).order_by('-id')
        elif request.user.corporate_business:
            transactions = Transaction.objects.filter(corporate_agency=request.user.corporate_business.id).order_by('-id')
    # if users is not None:
    #     paginator = Paginator(users, 10)
    #     page = request.GET.get('page')
    #     users = paginator.get_page(page)
    context = {
        'users': users,
        'transactions': transactions,
        'user_permissions_codenames': user_permissions_codenames
    }
    return render(request, 'super/transactions.html', context)


@login_required(login_url='signin')
def delete_transaction(request, transaction_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if 'tyktt_delete_transactions' in user_permissions_codenames or request.user.is_superuser:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if request.method == 'POST':
            transaction.delete()
            return redirect('transactions')

        return redirect('transactions')
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('transactions')


#LIST VIEW
@user_passes_test(lambda u: u.is_superuser, login_url="signin")
def pay_small_small_list(request):
    payment_transaction_record = Pay_small_small.objects.all()
    
    
    context ={
        "records": payment_transaction_record,
        
    }
    return render(request, "paysmallsmall/pay_small_small_list.html", context)
    


#create VIEW
@user_passes_test(lambda u: u.is_superuser, login_url="signin")
def pay_small_small_create(request):
    if request.method == "POST":
            form = PaySmallSmallForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect("pay_small_small_list")
    else:
            form = PaySmallSmallForm()
    
    # else:
    #     messages.error(request, 'You Do not have permission to perform this action')
    #     return redirect('pay_small_small_list')
        
    context ={
            "form": form,
        }
    return render(request, "paysmallsmall/pay_small_small_form.html", context)

#UPDATE VIEW
@user_passes_test(lambda u: u.is_superuser, login_url="signin")
def pay_small_small_update(request, id):

    if request.user.is_superuser:
        record = get_object_or_404(Pay_small_small, id=id)
        
        if request.method == "POST":
            form = PaySmallSmallForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
                return redirect("pay_small_small_list")
        else:
            form = PaySmallSmallForm(instance=record)
                
        context = {
            'form': form,
            "id": id
    }
        
    return render(request, "paysmallsmall/pay_small_small_update_form.html", context)

#DELETE VIEW
@user_passes_test(lambda u: u.is_superuser, login_url="signin")
def pay_small_small_delete(request: HttpRequest, id: str):
    record = get_object_or_404(Pay_small_small, id=id)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Record deleted successfully")
        return redirect("pay_small_small_list")
        
    messages.error(request, "Record deletion failed")
    context = {
        "record": record,
    }
    return redirect('pay_small_small_list')


#paystack 
@csrf_exempt
def initialize_payment(request: HttpRequest) -> JsonResponse:
    
    paystack = Paystack("PAYSTACK_SECRET_KEY")
    
    # if request.method != "POST":
    #     return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
    
    
    try:
        # email:str| None  =request.POST.get("email")
        # amount:int| None = int(request.POST.get("amount"))
        email = "customer@example.com"
        amount = 500000  # Amount in kobo (5000 Naira = 500,000 kobo)
      
        
        
    except json.JSONDecodeError as e:
        return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"}, status=500)
    
    if not email or not amount:
        return JsonResponse({"status": "error", "message": "Email and amount are required"}, status=400)
    # Example data for the payment
    
    transaction = PayStackTransaction.objects.create(
        email = email,
        amount = amount,
        status = "Pending",
        
    )
    # Generate a payment link
    payment_response = paystack.create_payment_link(
        name="Payment for Services",
        email=email,
        description="Payment for XYZ services",
        amount=amount,
        redirect_url="http://127.0.0.1:8000/transaction/verify-payment/"
    )
    
    # Check if the payment link was generated successfully
    if isinstance(payment_response, dict) and payment_response.get("status") == True:
        #update the database with the reference number:
        transaction.reference = payment_response['data']['reference']
        transaction.save()
        # Redirect user to the Paystack payment page
        payment_url = payment_response['data']['authorization_url']
        return HttpResponseRedirect(payment_url)
    
    # If there was an error, return an error response
    return JsonResponse({"status": "error", "message": "Unable to initialize payment"})


@csrf_exempt
def verify_payment(request: HttpRequest) -> JsonResponse:
    reference = request.GET.get("reference")
    logger.debug(f"Logger before the reference: {reference}")
    
    if not reference:
        return JsonResponse({"status": "error", "message": "Reference not provided"})
    try:
        #create an instance and verify the transaction
        transaction = get_object_or_404(PayStackTransaction, reference=reference)
        paystack = Paystack()
        transaction_status = paystack.verify_payment(reference)
        if transaction_status.get("status") and transaction_status.get('data')['status'] == "success" and not transaction.used:
            transaction.status = "Successful"
            transaction.amount = transaction_status.get('data')['amount'] / 100
            subject = "Soft Crown Booking Placement"
            transaction.used = True
            pay_small_small = Pay_small_small.objects.filter(booking=transaction.booking, paystack=transaction).first()
            if pay_small_small:
                if pay_small_small.balance > 0:
                    pay_small_small.paid = float(transaction.amount)
                    pay_small_small.balance = float(pay_small_small.amount) - float(transaction.amount)
                    pay_small_small.save()
            # html_message = render_to_string('emails/welcome_email.html', {'user': self})
            # plain_message = strip_tags(html_message)
            booking = get_object_or_404(Booking, id=transaction.booking.id)
            send_booking_email(request, booking.response, transaction.email, booking)
        elif transaction.used == True:
            pass
        else:
            transaction.status = "Failed"
        transaction.save()


        context = {
            "transaction": transaction_status,
            "booking": transaction.booking,
        }
        return render(request, "super/view_itinerary.html", context)
    except PayStackTransaction.DoesNotExist:
        logger.error(f"Transaction with reference number: {reference}, was not found.")
        return JsonResponse({"status": "error", "message": f"Transaction with reference number: {reference}, was not found."}, status=404)
    except Exception as e:
        logger.error(f"Error verifying payment with reference number: {reference}.")
        return JsonResponse({"status": "error", "message": f"Payment verification failed: {str(e)}"})


@csrf_exempt
@require_POST
def paystack_webhook(request: HttpRequest) -> JsonResponse:
    
    """
    Handle Paystack webhook events. Exempt from CSRF as Paystack will not send a CSRF token.
    """
  #! we are not using this for now, but the post request should be uncommented once we start testing the webhook with actual forms 
  #! that leads to the initialization of payment.
    logger.info(f"Request received: {request.method} {request.path}")
    try:
        data = json.loads(request.body)
        logger.info(f"Logger after the data: {data}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
     
    
    event = data.get("event")
    event_data = data.get("data", {})
    
    logger.info(f"Logger after the event: {event}")
    
    if event == "charge.success":
        # print("charge here")


        return handle_charge_success(event_data)
    elif event == "charge.failed":
        return handle_charge_failed(event_data)
    
    else:
        #log unhandled error
        # print(f"Unhandled event type: {event}")
        return JsonResponse({"status": "error", "message": f"Unhandled event type: {event}"}, status=400)
        
    

def handle_charge_success(event_data: Dict[str, Any]) -> JsonResponse:
    """
    handle charge success event
    """
    
    reference = event_data.get("reference")
    logger.info(f"Logger after the reference: {reference}")
    if not reference: 
        # print("reference was not found in charge.success event")
        return JsonResponse({'status':"failed", "message":"Reference was not found"})
    
    try:
        transaction = get_object_or_404(PayStackTransaction, reference=reference)
        transaction.status = "Successful"
        transaction.save()
        logger.info(f"Transaction with reference number: {reference}, was found and updated to successful.")
    except PayStackTransaction.DoesNotExist as e:
        # print(f"Transaction with reference number: {reference}, was not found.")
        return JsonResponse({'status':"error","message":"Transaction does not exist"})
        


def handle_charge_failed(event_data: Dict[str, Any]) -> JsonResponse:
    """
    handle charge failed event
    """
    reference = event_data.get("reference")
    if not reference: 
        logger.info("reference was not found in charge.failed event")
        return
    
    try:
        transaction = get_object_or_404(PayStackTransaction, reference=reference)
        transaction.status = "Failed"
        transaction.save()  
    except PayStackTransaction.DoesNotExist:
        logger.debug(f"Transaction with reference number: {reference}, was not found.")
        
    
def flutter_payment_form(request):
    """
    Render the Flutterwave Payment Form for manual testing.
    """
    # Get parameters from the request, providing default values if needed
    amount = request.GET.get('amount')
    email = request.GET.get('email')
    phone_number = request.GET.get('phone_number')
    booking_id = request.GET.get('booking')
    pay_small_small = request.GET.get('first_pay')

    # Retrieve the booking instance based on the booking ID
    booking_instance = get_object_or_404(Booking, id=booking_id) if booking_id else None

    # Create an instance of the form
    form = FlutterPaymentForm(initial={
        'email': email,  # Set the email from the request
        'phone_number': phone_number,  # Include phone number if provided
        'amount': amount,  # Set the amount if provided
        'booking': booking_instance.id if booking_instance else '',  # Set the booking ID if available
    })

    # Prepare the context to pass to the template
    context = {
        'form': form,
        'pay_small_small': pay_small_small,
    }

    return render(request, 't/flutter_test_form.html', context)

def flutter_payment(request: HttpRequest) -> JsonResponse:
    """
    Initialize a Flutterwave payment and redirect to the payment page.
    Be sure to use localhost:8000
    Args:
        request (HttpRequest): Django HTTP request object.

    Returns:
        JsonResponse or HttpResponseRedirect: Redirect to Flutterwave payment page or JsonResponse with error.
    """
    if request.method != 'POST':
        logger.warning("Invalid HTTP method used for flutter_payment.")
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

    form = FlutterPaymentForm(request.POST)
    if not form.is_valid():
        logger.info(f"Invalid payment form data: {form.errors}")
        return JsonResponse({
            "status": "error",
            "message": "Invalid input data.",
            "errors": form.errors
        }, status=400)
        
    # print("form is valid")
    # print(form.cleaned_data)
    amount = form.cleaned_data['amount']
    email = form.cleaned_data['email']
    phone_number = form.cleaned_data['phone_number']
    booking = form.cleaned_data['booking']
    if amount <= 0:
        logger.error("Invalid amount provided.")
        return JsonResponse({"status": "error", "message": "Amount must be greater than zero."}, status=400)

    secret_key = os.getenv('FLW_SECRET_KEY')
    if not secret_key:
        logger.error("Flutterwave Secret Key not found in environment variables.")
        return JsonResponse({"status": "error", "message": "Payment configuration error."}, status=500)
    # print("secret key found")
    # Generate a unique transaction reference
    tx_ref = f"tx-{uuid4()}"

    try:
        
        with db_transaction.atomic():
            flutter_transaction = FlutterwaveTransaction.objects.create(
                tx_ref=tx_ref,
                phone_number=phone_number,
                email=email,
                amount=amount,
                currency="NGN",
                status="Pending",
                booking=booking
            )
            if request.POST.get("pay_small_small") != "None":
                pay_small_small = get_object_or_404(Pay_small_small, id=request.POST.get("pay_small_small"))
                pay_small_small.flutterwave = flutter_transaction
                pay_small_small.save()
    except Exception as e:
        logger.exception("Error creating Flutterwave transaction.")
        return JsonResponse({"status": "error", "message": "Internal server error."}, status=500)

    # Prepare payload for Flutterwave's API
    base_url = request.build_absolute_uri('/')
    if '127.0.0.1' in base_url:
        base_url = base_url.replace('127.0.0.1', 'localhost')

    redirect_url = f"{base_url}transaction/payment-callback"
    payload: Dict[str, Any] = {
        "tx_ref": tx_ref,
        "amount": str(amount),
        "currency": flutter_transaction.currency,
        # "redirect_url": request.build_absolute_uri(reverse("flutterwave_payment_callback")),
        "redirect_url": redirect_url,
        "customer": {
            "email": email,
            "phone_number": phone_number
        },
        "payment_options": "card, banktransfer, ussd",
        "configurations": {
            "session_duration": 10,
            "max_retry_attempt": 5
        },
        "customizations": {
            "title": "Your App Payment",
            "description": "Payment for services",
        },
        "meta": {
       "integration": "django_flutterwave_integration"
   },
    }

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        # print("response:", response)
        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"Flutterwave response: {response_data}")

        if response_data.get("status") == "success":
            payment_link = response_data.get('data', {}).get('link')
            if payment_link:
                logger.info(f"Redirecting to Flutterwave payment link: {payment_link}")
                return redirect(payment_link)
            else:
                logger.error("Payment link not found in Flutterwave response.")
                return JsonResponse({"status": "error", "message": "Payment link not available."}, status=500)
        else:
            error_message = response_data.get("message", "Payment initialization failed.")
            logger.error(f"Flutterwave payment initialization failed: {error_message}")
            return JsonResponse({"status": "error", "message": error_message}, status=400)

    except requests.exceptions.HTTPError as http_err:
        logger.exception(f"HTTP error occurred during Flutterwave payment initialization: {http_err}")
        return JsonResponse({"status": "error", "message": "Payment service error."}, status=502)
    except requests.exceptions.RequestException as req_err:
        logger.exception(f"Request exception during Flutterwave payment initialization: {req_err}")
        return JsonResponse({"status": "error", "message": "Payment service unavailable."}, status=503)
    except Exception as e:
        logger.exception("An unexpected error occurred during Flutterwave payment initialization.")
        return JsonResponse({"status": "error", "message": "An unexpected error occurred."}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def flutter_payment_callback(request)-> JsonResponse:
    
    try:
        secret_key = os.getenv('FLW_SECRET_KEY')
        if not secret_key:
            raise ValidationError("Payment configuration error")

        # Get callback parameters
        tx_ref = request.GET.get("tx_ref")
        status = request.GET.get("status")
        transaction_id = request.GET.get("transaction_id")

        if not all([tx_ref, status, transaction_id]):
            return render(request, "payment/payment_status.html", {
                "status": "error",
                "message": "Invalid callback parameters"
            })

        # Fetch transaction
        transaction = get_object_or_404(FlutterwaveTransaction, tx_ref=tx_ref)

        # Prepare verification request
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }

        # Verify transaction with Flutterwave
        verify_response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
            headers=headers,
            timeout=30
        )
        verify_response.raise_for_status()
        verification_data:JsonResponse = verify_response.json()
        pay_small_small = Pay_small_small.objects.filter(booking=transaction.booking, flutterwave=transaction).first()
        print(pay_small_small)
        # Process verification result
        if (verification_data.get('status') == "success" and
            verification_data['data']['status'] == "successful" and
            verification_data['data']['amount'] == transaction.amount and
            verification_data['data']['currency'] == transaction.currency):
            
            # Update transaction as successful
            with db_transaction.atomic():
                transaction.status = "successful"
                transaction.flw_ref = verification_data['data'].get('flw_ref')
                transaction.transaction_id = transaction_id
                # transaction.verified = True
                
                # # Add additional payment details
                transaction.payment_type = verification_data['data'].get('payment_type')
                transaction.verified  = True
                transaction.processor_response = verification_data['data'].get('processor_response')
                transaction.app_fee = verification_data['data'].get('app_fee')
                transaction.merchant_fee = verification_data['data'].get('merchant_fee')
                transaction.charged_amount = verification_data['data'].get('charged_amount')
                transaction.used = True
                if pay_small_small:
                    if pay_small_small.balance > 0 and not transaction.used:
                        pay_small_small.paid = float(transaction.amount)
                        pay_small_small.balance = float(pay_small_small.amount) - float(transaction.amount)
                        pay_small_small.save()
                transaction.save()
                subject = "Soft Crown Booking Placement"
                plain_message = f"Your Booking  has been placed  successfully - {transaction.booking.formatted_id}"
                from_email = 'jomivictravels@quickwavetech.com'
                recipient_list = [transaction.email]

                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    recipient_list,
                    # html_message=html_message,
                    fail_silently=False,
                )
                
            
        else:
            # Update transaction as failed
            transaction.status = "Failed"

            transaction.save()

        # Prepare template context
        context = {
            "transaction": transaction,
            "status": transaction.status,
            "booking": transaction.booking,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "reference": transaction.tx_ref,
            "payment_type": verification_data['data'].get('payment_type')
        }

        return render(request, "super/view_itinerary.html", context)

    except requests.exceptions.RequestException as e:
        return render(request, "t/payment_status.html", {
            "status": "error",
            "message": "Failed to verify payment"
        })
    except Exception as e:
        return render(request, "t/payment_status.html", {
            "status": "error",
            "message": "An error occurred while processing payment"
        })
        
        
"""
webhook needs testing
"""
@require_POST
@csrf_exempt
def flw_payment_webhook(request:HttpRequest)->HttpResponse:
    """
    Handle Flutterwave payment webhooks.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        HttpResponse: 200 if processed successfully, appropriate error code otherwise
    """
    try:
        secret_key:str = os.getenv('FLW_SECRET_KEY')
        secret_hash:str = os.getenv('FLW_SIGNATURE_SECRET_HASH')
        
        """
        Replace secret hash to using hmac for verifying signatures
        """

        if not all([secret_key, secret_hash]):
            logger.error("Missing required environment variables")
            print('1')
            return HttpResponse(status=500)
        
        # logger.info("Logging the secret hash",secret_hash)
        signature = request.headers.get('verif-hash')
        computed_hmac = hmac.new(
            key=secret_hash.encode(),
            msg=request.body,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        if not signature :
            logger.warning("Missing webhook signature")
            return HttpResponse(status=401)
        

        try:
        
            payload:Dict[str, Any] = json.loads(request.body)
            logger.info(f"Received the webhook event: {payload.get('event')}")
            
        except json.JSONDecodeError as e:
            logger.error("Invalid Json payload")
            return HttpResponse(status=400)
            
        
        event_type = payload.get('event')
        if event_type != "charge.completed":
            logger.info("Ignoring non-payment webhook event ", event_type)
            return HttpResponse(status=200)
        #get payload_data
        transaction_data:Dict[str, Any] = payload.get('data')
        if not transaction_data:
            logger.error("Missing transaction data in webhook payload")
            return HttpResponse(status=400)
        
        flw_ref:str = transaction_data.get('flw_ref')
        tx_ref:str = transaction_data.get('tx_ref')
        status:str = transaction_data.get('status')
        amount:float = float(transaction_data.get('amount'))
        currency:str = transaction_data.get('currency')
        transaction_id:str = transaction_data.get('id')
        
        if not all([flw_ref, tx_ref, status, amount, currency]):
            logger.error("Missing required transaction details in webhook payload")
            return HttpResponse(status=400)
        
        #fetch Transaction from database
        try:
            transaction = FlutterwaveTransaction.objects.select_for_update().get(
                tx_ref=transaction_data['tx_ref'])
            
            if not transaction_id and transaction.transaction_id != transaction_id:
                logger.error("Transaction ID not found in webhook payload.")
                logger.error(f"Transaction ID in database: {transaction.transaction_id}")
                logger.error(f"Transaction ID in webhook payload: {transaction_id}")
                return HttpResponse(status=400)
        except FlutterwaveTransaction.DoesNotExist:
            logger.error(f"Transaction with flw_ref {flw_ref} not found.")
            return HttpResponse(status=404)
        
        headers: Dict[str, str] = {
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            }
        
        try:
            response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
            headers=headers,
            timeout=30
        )
            response.raise_for_status()
            response_data = response.json()
            logger.info("response_data:", response_data)
            
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch transaction from flutterwave: ", e)
            return HttpResponse(status=500)
        
        if (response_data.get('status') == 'success' and response_data['data']['status'] == 'successful'
            and float(response_data['data']['amount']) == float(transaction.amount)
            and response_data['data']['currency'] == transaction.currency):
                        # Update transaction status
                with db_transaction.atomic():
                    transaction.status = 'successful'
                    transaction.payment_type = response_data['data'].get('payment_type')
                    transaction.charged_amount = response_data['data'].get('charged_amount')
                    transaction.flw_ref = flw_ref
                    transaction.processor_response = response_data['data'].get('processor_response')
                    transaction.verified = True
                    transaction.save()
                    booking = get_object_or_404(Booking, id=transaction.booking)
                    send_booking_email(request, booking.response, transaction.email, booking)
                return HttpResponse(status=200)
        else:
            with db_transaction.atomic():
                transaction.status = 'failed'
                transaction.verified = False
                transaction.save()
            
            logger.warning("Payment verification failed for transaction %s", tx_ref)
        
    except Exception as e:
        logger.error("An error occurred while processing payment webhook: ", e)
        return HttpResponse(status=500)
    

def test_flutterwave(request):
    return render(request, 'payments/payment_flutterwave.html')

@login_required(login_url='signin')
def manual_payment(request):
    if request.method == "POST":
        action = request.POST.get('action')
        booking = get_object_or_404(Booking, id=request.POST.get('booking_id'))
        pay_small_small = get_object_or_404(Pay_small_small, id=request.POST.get("paysmall_id"))
        if action == "pay_small_small":
            manual_payment = ManualPayment.objects.create(
                booking=booking,
                amount=request.POST.get("amount"),
                date_payment=request.POST.get("date"),
                Pay_small_small=pay_small_small,
                currency=booking.currency,
            )
            if float(pay_small_small.balance) <= float(manual_payment.amount):
                manual_payment.amount = pay_small_small.balance
                manual_payment.save()
            if pay_small_small.balance:
                pay_small_small.balance = float(pay_small_small.balance) - float(manual_payment.amount)
            else:
                pay_small_small.balance = float(pay_small_small.amount) - float(manual_payment.amount)
            if pay_small_small.paid:
                pay_small_small.paid = float(manual_payment.amount) + float(pay_small_small.paid)
            else:
                pay_small_small.paid = float(manual_payment.amount)
            if pay_small_small.balance < 0:
                pay_small_small.balance = 0
            pay_small_small.save()
            messages.success(request, "Record Added successfully")
        elif action == 'send_reminder':
            subject = "Payment Reminder for Your 'Pay in Bit' Flight Reservation"
            booking = get_object_or_404(Booking, id=pay_small_small.booking_id)
            # Use an f-string to format the message with your placeholders
            message = (
                f"Dear {pay_small_small.first_name},\n\n"
                "We hope this message finds you well! This is a friendly reminder regarding the next payment "
                "installment for your flight reservation with our 'Pay in Bit' option.\n\n"
                "Reservation Details:\n\n"
                f"    Trip ID: {booking.formatted_id}\n"  # Replace with the actual booking ID attribute
                f"    Next Payment Amount: {pay_small_small.currency} {pay_small_small.balance:,.2f}\n"
                f"    Due Date: {pay_small_small.due_date}\n\n"  # Replace with the actual due date attribute
                "If you have any questions or need assistance with the payment process, feel free to contact us. "
                "We’re here to help and want to make sure your travel plans proceed smoothly!\n\n"
                "Thank you for choosing us for your travel needs. We look forward to helping you complete your "
                "booking and making your journey a memorable one.\n\n"
                "Warm regards,\n"
                "Jomivic Travelss\n"
                "Info@jomivictravels.com, +23412934120"  # Replace with the actual contact info
            )

            # Send the email
            send_mail(
                subject=subject,
                message=message,
                from_email="jomivictravels@quickwavetech.com",
                recipient_list=[pay_small_small.email],
                fail_silently=False,
            )
            messages.success(request, "Reminder Sent successfully")
        return redirect('bookinginfo', booking.id)

    return redirect('/')

