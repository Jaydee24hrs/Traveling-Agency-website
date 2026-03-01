import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.core.mail import BadHeaderError
from django.db.models import Q
from django import template
from django.urls import reverse
import random
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from rest_framework.renderers import JSONRenderer
from dotenv import load_dotenv
from User.models import CustomUser, Customer
from django.contrib.auth.models import Group, Permission
from User.views import convert_to_date
from Transaction.models import Transaction
from Booking.models import Booking
from Markup.models import ExchangeRate, ExchangeRateExclution, MarkupRuleTyktt, TykttMarkUp
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.core.mail import send_mail
from jomivictravels.settings import BASE_DIR
# from datetime import datetime

load_dotenv()
# ======================================  SIGNUP SECTION  STARTS  ==================================================

# For Alert Starts
def my_view(request):
    # Some logic to determine the type of message
    messages.success(request, 'This is a success message.')
    messages.error(request, 'This is an error message.')
    messages.warning(request, 'This is a warning message.')
    messages.info(request, 'This is an info message.')
    return render(request, 'my_template.html')


# For Alert Ends


# Terms and Conditions Starts
def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')

# Terms and Conditions Ends

# Privacy Policy Starts
def privacy_legal(request):
    return render(request, 'privacy_legal.html')


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
# Privacy Policy Ends


# SignIn Starts
def signin(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        remember_password = request.POST.get('remember_password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # if user.is_verified:
            login(request, user)
            if remember_password:
                request.session['remember_password'] = True
                request.session['email'] = email
                return redirect('dashboard')
            else:
                request.session.pop('remember_password', None)
                request.session.pop('email', None)
            return redirect('dashboard')
            # else:
            #     messages.error(request, 'Verify Email')
            #     login(request, user)
            #     return redirect(reverse('verify_otp'))
        else:
            messages.error(request, 'Invalid email or password')
    else:
        # Check if user is authenticated and populate email field
        if request.user.is_authenticated:
            email = request.session.get('email', '')
            password = request.session.get('password', '')
        else:
            email = ''
            password = ''

    return render(request, 'signin.html')

# SignIn Ends


# SignOut Page Starts
def signout(request):
    logout(request)
    request.session.pop('remember_password', None)
    request.session.pop('email', None)
    return redirect('signin')


# SignOut Page Ends


# Forgot Password Starts
def forgot(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = CustomUser.objects.filter(Q(email=data))
            current_site = request.get_host()
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    plaintext = template.loader.get_template('emails/password_reset_email.txt')
                    htmltemp = template.loader.get_template('emails/password_reset_email.html')
                    c = {
                        "email": user.email,
                        'domain': current_site,
                        'site_name': 'Tyktt',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                    }
                    text_content = plaintext.render(c)
                    html_content = htmltemp.render(c)
                    try:
                        msg = EmailMultiAlternatives(subject, text_content, 'Tyktt <jomivictravels@quickwavetech.com>',
                                                     [user.email], headers={'Reply-To': 'jomivictravels@quickwavetech.com'})
                        msg.attach_alternative(html_content, "text/html")
                        msg.send()
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("/password_reset/done/")
            messages.error(request, 'No user exist with this email address')
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="forgot_password.html",
                  context={"password_reset_form": password_reset_form})


# Dashboard starts
def dashboard(request):
    user = request.user
    # Fetch all permissions directly assigned to the user and get only 'codename'
    user_permissions_codenames = user.user_permissions.values_list('codename', flat=True)

    context = {
        'user': user,
        'user_permissions_codenames': user_permissions_codenames
    }
    return render(request, 'super/dashboard.html', context)


# Dashboard ends




@login_required(login_url='signin')
def bookinginfo(request, user_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = get_object_or_404(User, pk=user_id)

    context = {
        "user": user,
        "user_permissions_codenames":user_permissions_codenames
    }

    return render(request, 'super/bookinginfo.html', context)


# Manage Bookings Ends


# Teams Starts
@login_required(login_url='signin')
def teams(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = request.user
    teams = CustomUser.objects.filter(is_superuser=False)
    if teams:
        paginator = Paginator(teams, 10)
        page = request.GET.get('page')
        teams = paginator.get_page(page)

    context = {
        'teams': teams,
        'user_permissions_codenames': user_permissions_codenames
    }
    return render(request, 'super/teams.html', context)


# Teams Ends



# Settings Ends

# Markup Starts
def markup(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    # markup_rules = MarkupRuleTyktt.objects.all()
    markup_rules = None
    markup_rules = TykttMarkUp.objects.prefetch_related('tyktt_commission').order_by("-created_at")
    exclutions = ExchangeRateExclution.objects.all()
    rates = ExchangeRate.objects.using("default").all()
    # tyktt_markup_rules = None
    total_count = 0
    page = request.GET.get('page')
    context = {
        'user_permissions_codenames': user_permissions_codenames,
        'markup_rules': markup_rules,
        'total_count': total_count,
        'rates': rates,
        'exclutions': exclutions,
    }
    return render(request, 'super/markup.html', context)


# Markup Ends

def contactUs(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = request.user

    if request.method == "POST":
        # Get form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company_name = request.POST.get('company_name')
        form_topic = request.POST.get('form_topic')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        email = user.email  # Assuming the user's email is available

        # Handle file attachment (if any)
        file = request.FILES.get('customFile')

        # Create the email body
        email_body = f"""
        First Name: {first_name}
        Last Name: {last_name}
        Company Name: {company_name}
        Form Topic: {form_topic}
        Subject: {subject}
        Description: {description}
        """

        # Prepare the email
        if form_topic in ['technical issue']:
            email_message = EmailMessage(
                subject=f"Contact Us Form: {subject}",
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['feedback.ng@tyktt.com'],
                reply_to=[email],
            )
        else:
            email_message = EmailMessage(
                subject=f"Contact Us Form: {subject}",
                body=email_body,
                from_email='jomivictravels@quickwavetech.com',
                to=['technicalissue@tyktt.com'],
                reply_to=[email],
            )

        # Attach file if provided
        if file:
            email_message.attach(file.name, file.read(), file.content_type)

        # Send the email
        email_message.send()

        # Redirect to a success page (or render a success message)
        return redirect('contactUs')  # Replace with your success URL

    # Render the form page if it's a GET request
    context = {
        'user': user,
        'user_permissions_codenames': user_permissions_codenames,
    }
    return render(request, 'super/contactUs.html', context)



def crm(request):
    customers = Customer.objects.all()

    context = {
        'customers': customers
    }
    
    return render(request, 'super/crm.html', context)



def viewItinerary(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    contex = {
        "booking": booking,
    }

    return render(request, 'super/view_itinerary.html', contex)


def get_json_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:  # Use utf-8-sig to handle BOM and special characters
            data = json.load(file)  # Load JSON content
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except UnicodeDecodeError as e:
        print(f"Error decoding file due to character encoding: {e}")
        return None

def all_countries(request):
    file_path = os.path.join(BASE_DIR, 'countries.json')  # Adjust the path as necessary
    data = get_json_data(file_path)
    if data:
        return JsonResponse(data, safe=False)  # Return as JSON response
    else:
        return JsonResponse({"error": "Failed to load data"}, status=500)



def about(request):
    
    return render(request, 'super/about.html')


def service(request):
    
    return render(request, 'super/service.html')


def contact(request):
    if request.method == "POST":
        # Get form data from the request
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email_address")
        subject = request.POST.get("subject")
        description = request.POST.get("description")

        # Handle file attachment (if any)
        file = request.FILES.get("customFile")

        # Create the email body
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    color: #333333;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border: 1px solid #dddddd;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                h2 {{
                    color: #003399;
                    border-bottom: 2px solid #003399;
                    padding-bottom: 5px;
                    margin-bottom: 20px;
                }}
                p {{
                    margin: 10px 0;
                    font-size: 16px;
                }}
                .highlight {{
                    font-weight: bold;
                    color: #003399;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <h2>Contact Us Form Details</h2>
                <p><span class="highlight">First Name:</span> {first_name}</p>
                <p><span class="highlight">Last Name:</span> {last_name}</p>
                <p><span class="highlight">Phone Number:</span> {phone_number}</p>
                <p><span class="highlight">Email:</span> {email}</p>
                <p><span class="highlight">Subject:</span> {subject}</p>
                <p><span class="highlight">Description:</span><br>{description}</p>
            </div>
        </body>
        </html>
        """


        email_message = EmailMessage(
            subject=f"Contact Us Form: {subject}",
            body=email_body,
            from_email="jomivictravels@quickwavetech.com",
            to=["chinedue856@gmail.com"],
            reply_to=[email],
        )
        email_message.content_subtype = "html"  # Set the content type to HTML


        # Attach file if provided
        if file:
            email_message.attach(file.name, file.read(), file.content_type)

        # Send the email
        email_message.send()

    return render(request, 'super/contact.html')


def faq(request):
    
    return render(request, 'super/faq.html')

def portfolio(request):
    
    return render(request, 'super/portfolio.html')

def blog(request):
    
    return render(request, 'super/blog.html')

def blog_information(request):
    
    return render(request, 'super/blog_information.html')

# Hotels

def hotel_details(request):
    
    return render(request, 'super/hotel_details.html')

def hotel_info(request):
    
    return render(request, 'super/hotel_info.html')

def hotel_book(request):
    
    return render(request, 'super/hotel_book.html')

def hotel_checkout(request):
    
    return render(request, 'super/hotel_checkout.html')

def hotel_page(request):
    
    return render(request, 'super/hotel_page.html')


# Tours
def tour_details(request):
    
    return render(request, 'super/tour_details.html')

def tour_info(request):
    
    return render(request, 'super/tour_info.html')

def tour_book(request):
    
    return render(request, 'super/tour_book.html')

def tour_checkout(request):
    
    return render(request, 'super/tour_checkout.html')

def tour_page(request):
    
    return render(request, 'super/tour_page.html')


# Resturant
def resturant_details(request):
    
    return render(request, 'super/resturant_details.html')

def resturant_info(request):
    
    return render(request, 'super/resturant_info.html')

def resturant_checkout(request):
    
    return render(request, 'super/resturant_checkout.html')

def resturant_page(request):
    
    return render(request, 'super/resturant_page.html')


# car
def car_details(request):
    
    return render(request, 'super/car_details.html')

def car_info(request):
    
    return render(request, 'super/car_info.html')

def car_book(request):
    
    return render(request, 'super/car_book.html')

def car_checkout(request):
    
    return render(request, 'super/car_checkout.html')

def car_page(request):
    
    return render(request, 'super/car_page.html')

def refund_and_cancellation(request):
    
    return render(request, 'super/refund_and_cancellation.html')

