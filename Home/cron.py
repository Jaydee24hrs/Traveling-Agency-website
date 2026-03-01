from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from Booking.models import Booking
from Transaction.models import Pay_small_small
from django.core.mail import send_mail

def my_scheduled_job():
    # Get today's date
    today = timezone.now().date()
    # Calculate date range: today and the next two days
    start_date = today
    end_date = today + timedelta(days=2)
    
    # Fetch payments with due dates in the range of 0 to 2 days from today
    all_pay_small = Pay_small_small.objects.filter(balance__gt=0, due_date__range=[start_date, end_date])
    
    for pay_small in all_pay_small:
        if pay_small.email:  # Check if an email address is available
            subject = "Upcoming Payment Reminder for Your 'Pay in Bit' Flight Reservation"
            booking = get_object_or_404(Booking, id=pay_small.booking_id)
            
            message = (
                f"Dear {pay_small.first_name},\n\n"
                "We hope this message finds you well! This is a friendly reminder regarding your upcoming payment "
                "installment for your flight reservation with our 'Pay in Bit' option.\n\n"
                "Reservation Details:\n\n"
                f"    Trip ID: {booking.formatted_id}\n"  # Replace with the actual booking ID attribute
                f"    Upcoming Payment Amount: {pay_small.currency} {pay_small.balance:,.2f}\n"
                f"    Payment Due Date: {pay_small.due_date}\n\n"
                "If you have any questions or need assistance with the payment process, feel free to contact us. "
                "We’re here to help and want to make sure your travel plans proceed smoothly!\n\n"
                "Thank you for choosing us for your travel needs. We look forward to helping you complete your "
                "booking and making your journey a memorable one.\n\n"
                "Warm regards,\n"
                "Jomivic Travel\n"
                "Info@jomivictravels.com, +23412934120"
            )

            # Send the email
            send_mail(
                subject=subject,
                message=message,
                from_email="jomivictravels@quickwavetech.com",
                recipient_list=[pay_small.email, "Info@jomivictravels.com"],
                fail_silently=False,
            )
        else:
            print(f"Warning: No email address found for {pay_small}.")
