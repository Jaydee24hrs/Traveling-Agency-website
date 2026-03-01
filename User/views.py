import datetime
import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.mail import send_mail, EmailMessage
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import CustomUserForm, ChangePasswordForm
from .models import CustomUser, OTP

def convert_to_date(date_string):
    """
    Convert a date string in the format "Month day, year" or "Mon. day, year" to a datetime object.

    Args:
    date_string (str): The date string to convert.

    Returns:
    datetime: The corresponding datetime object.
    """
    date_formats = ["%B %d, %Y", "%b %d, %Y"]  # Full month name and abbreviated month name

    # Replace any possible abbreviations or punctuations (e.g., "Dec." to "Dec")
    cleaned_date_string = date_string.replace(".", "")

    for date_format in date_formats:
        try:
            # Parse the date string into a datetime object
            date_object = datetime.datetime.strptime(cleaned_date_string, date_format)
            return date_object
        except ValueError:
            continue
    return None


@login_required(login_url='signin')
def create_team(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = request.user
    if user.is_superuser:
        if request.method == 'POST':
            # user = request.user
            user_id = request.POST.get('user_data')
            email = request.POST.get('email')
            corporate_business = None
            user_type = None
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, f"User {email} already exists.")
                return redirect('teams')

            # if user.is_superuser or user.user_type == "tyktt":
            #     user_type = "tyktt"
            #     if user.corporate_business:
            #         corporate_business = Corporate_Business.objects.get(id=user.corporate_business.id)
            # elif user.user_type == "affiliate":
            #     if user.corporate_business:
            #         user_type = "affiliate"
            #         corporate_business = Corporate_Business.objects.get(id=user.corporate_business.id)
            # else:
            #     return redirect('teams')

            # Generate a random password
            random_password = get_random_string(length=8)
            access_type = "User"
            if request.POST.get('access_type'):
                access_type = request.POST.get('access_type')
            elif request.POST.get('access_type_affiliate'):
                access_type = request.POST.get('access_type_affiliate')

            # Create the team member
            team = CustomUser.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                username=request.POST.get('email'),
                dob=request.POST.get('dob'),
                gender=request.POST.get('gender'),
                # user_type=user_type,
                position=request.POST.get('position'),
                phone=request.POST.get('phone'),
                means_of_identification="Passport",
                status="approved",
                access_type=access_type,
                profile_pic=request.FILES.get('member_doc', ''),
                means_of_identification_file=request.FILES.get('member_doc', ''),
                password=make_password(random_password)
            )


            # Generate password reset token and link
            token = default_token_generator.make_token(team)
            uid = urlsafe_base64_encode(force_bytes(team.pk))
            password_reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            # Send the password reset link to the user's email
            email_subject = 'Set Your Password'
            email_body = render_to_string('emails/password_reset_email_otp.html', {
                'user': team,
                'password_reset_link': password_reset_link,
            })

            email = EmailMessage(
                email_subject,
                email_body,
                'jomivictravels@quickwavetech.com',  # Replace with your email
                [team.email],
            )
            email.content_subtype = "html"
            email.send()

            team.save()
            messages.success(request, f"Team member {team.email} created successfully and password reset link sent.")
            return redirect('teams')  # Redirect to a view that lists teams or another appropriate view
        else:
            return redirect('teams')
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('teams')


@login_required(login_url='signin')
def update_team(request, user_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if any(permission in user_permissions_codenames for permission in
           ['tyktt_create_team_affiliate', 'tyktt_create_team', 'affiliate_create_team_member']) or request.user.is_superuser:
        if request.method == 'POST':
            # id = request.POST.get('team_id')
            team = CustomUser.objects.get(id=user_id)
            team.status = request.POST.get('status')
            team.gender = request.POST.get('gender')
            team.save()
            return redirect('teams')
        return redirect('teams')
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('teams')


@login_required(login_url='signin')
def update_team_info(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if any(permission in user_permissions_codenames for permission in
           ['tyktt_create_team_affiliate', 'tyktt_create_team', 'affiliate_create_team_member']) or request.user.is_superuser:
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            # id = request.POST.get('team_id')
            team = CustomUser.objects.get(id=user_id)
            # Update the fields with new values from the POST request
            team.first_name = request.POST.get('first_name', team.first_name)
            team.last_name = request.POST.get('last_name', team.last_name)
            if request.POST.get('dob'):
                team.dob = request.POST.get('dob', team.dob)
            team.gender = request.POST.get('gender', team.gender)
            team.position = request.POST.get('position')
            team.phone = request.POST.get('phone', team.phone)
            team.profile_pic = request.FILES.get('member_doc',team.profile_pic)
            print(request.POST.get('tyktt_office_id'))
            if team.access_type != request.POST.get('access_type'):
                team.user_permissions.clear()
            for permission, description in permissions_list:
                if request.POST.get(permission) == 'true':
                    try:
                        permissions_to_add = Permission.objects.filter(codename=permission)
                        for permission_add in permissions_to_add:
                            team.user_permissions.add(permission_add)
                    except Permission.DoesNotExist:
                        messages.error(request, f"Permission with codename '{permission}' does not exist.")
            team.save()
            messages.success(request, "Team Member updated Successfully")
            return redirect('teams')
        return redirect('teams')
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('teams')


@login_required(login_url='signin')
def update_team_business(request, team_id, company_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if any(permission in user_permissions_codenames for permission in
           ['tyktt_create_team_affiliate', 'tyktt_create_team', 'affiliate_create_team_member']):
        if request.method == 'POST':
            # id = request.POST.get('team_id')
            team = CustomUser.objects.get(id=team_id)
            team.status = request.POST.get('status')
            team.gender = request.POST.get('gender')
            team.save()
            return redirect('businessinfo', company_id)
        return redirect('businessinfo', company_id)
    else:
        messages.error(request, 'You Do not have permission to perform this action')
        return redirect('businessinfo', company_id)


def generate_otp():
    """Generate a 5-digit random OTP."""
    return random.randint(10000, 99999)


def send_otp_to_user(user, otp):
    """Placeholder function to send OTP to the user. Implement the actual logic."""
    send_mail(
        'OTP for Account Verification',
        f'Your OTP is: {otp}',
        'otp@tyktt.com',
        [user.email],
        fail_silently=False,
    )


def verify_otp(request):
    authenticated_user = request.user

    # Check if the user is already verified
    if authenticated_user.is_verified:
        return redirect('dashboard')

    if request.method == 'POST':
        # Get the individual digits of the OTP from the form inputs
        digit1 = request.POST['digit1']
        digit2 = request.POST['digit2']
        digit3 = request.POST['digit3']
        digit4 = request.POST['digit4']
        digit5 = request.POST['digit5']
        # Concatenate the digits to form the complete OTP
        otp_entered = digit1 + digit2 + digit3 + digit4 + digit5

        try:
            # Retrieve the OTP object for the authenticated user
            otp_record = OTP.objects.get(user=authenticated_user, otp=otp_entered, used=False)

            # Check if the OTP is within the 30-minute validity period
            if otp_record.created_on + timedelta(minutes=30) >= timezone.now():
                authenticated_user.is_verified = True
                authenticated_user.save()
                otp_record.used = True
                otp_record.save()
                return redirect('dashboard')
            else:
                # OTP has expired, regenerate and send a new one
                new_otp = generate_otp()
                otp_record.otp = new_otp
                otp_record.created_on = timezone.now()
                otp_record.used = False
                otp_record.save()
                send_otp_to_user(authenticated_user, new_otp)
                messages.error(request, 'OTP has expired. A new OTP has been sent to you.')
        except OTP.DoesNotExist:
            # Incorrect OTP, regenerate and send a new one
            new_otp = generate_otp()
            OTP.objects.create(user=authenticated_user, otp=new_otp)
            send_otp_to_user(authenticated_user, new_otp)
            messages.error(request, 'Incorrect OTP. A new OTP has been sent to you.')
    else:
        # If it's a GET request, you might want to send a new OTP
        new_otp = generate_otp()
        OTP.objects.create(user=authenticated_user, otp=new_otp)
        send_otp_to_user(authenticated_user, new_otp)
        messages.info(request, 'A new OTP has been sent to you.')

    return render(request, 'verify_email.html')


def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        print("jjjjjjjjj")
        remember_password = request.POST.get('remember_password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if remember_password:
                request.session['remember_password'] = True
                request.session['email'] = email
                return redirect('dashboard')
            else:
                request.session.pop('remember_password', None)
                request.session.pop('email', None)
                return redirect('dashboard')
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


# SignOut Page Starts
def signout(request):
    logout(request)
    request.session.pop('remember_password', None)
    request.session.pop('email', None)
    return redirect('signin')


@login_required(login_url='signin')
def profile(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = request.user
    user = CustomUser.objects.get(id=user.id)
    context = {
        'user': user,
        'user_permissions_codenames': user_permissions_codenames
    }

    return render(request, 'super/profile.html', context)


@login_required(login_url='signin')
def assign_user(request, user_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    team = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        if 'tyktt_assign_account_officer_affiliate' in user_permissions_codenames:
            get_agency = request.POST.get('agencySelect')
            return redirect('teams')
        else:
            messages.error(request, 'You Do not have permission to perform this action')
            return redirect('teams')
    return redirect('teams')


@login_required(login_url='signin')
def delete_user(request, user_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    team = get_object_or_404(CustomUser, pk=user_id)
    team.delete()
    return redirect('teams')


@login_required
def change_password(request):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        # Retrieve the user
        user = request.user

        # Check old password
        if not user.check_password(old_password):
            messages.error(request, 'Old password is incorrect')
            return redirect('profile')

        # Validate new passwords
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match')
            return redirect('profile')

        # Change password
        user.set_password(new_password1)
        user.save()
        update_session_auth_hash(request, user)  # Important to update session with new password
        messages.success(request, 'Your password was successfully updated!')
        return redirect('profile')  # Replace with your profile or home view name

    return redirect('profile')


def resend_password(request, user_id):
    user_permissions_codenames = request.user.user_permissions.values_list('codename', flat=True)
    user = get_object_or_404(CustomUser, pk=user_id)

    # Generate password reset token and link
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    password_reset_link = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )

    # Render the email template with the password reset link
    email_subject = 'Reset Your Password'
    email_body = render_to_string('emails/password_reset_email_otp.html', {
        'user': user,
        'password_reset_link': password_reset_link,
    })

    # Send the email
    email = EmailMessage(
        email_subject,
        email_body,
        'jomivictravels@quickwavetech.com',  # Replace with your email
        [user.email],
    )
    email.content_subtype = "html"
    email.send()

    messages.success(request, 'Password reset link sent successfully.')
    return redirect('teams')
