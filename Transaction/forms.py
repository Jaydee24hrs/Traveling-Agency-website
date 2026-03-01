from django import forms
from django.core.validators import EmailValidator
from .models import FlutterwaveTransaction, Pay_small_small, Transaction


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = ['transaction_date', 'booking_id', 'payment_method',
                  'amount', 'remark', 'description', 'status', 'currency']


class PaySmallSmallForm(forms.ModelForm):
    class Meta: 
        model = Pay_small_small
        fields = ['first_name', 'last_name', 'email', 'phone', 'amount']
        
        

class FlutterPaymentForm(forms.ModelForm):
    class Meta:
        model = FlutterwaveTransaction
        fields = ['amount', 'email', 'phone_number', 'booking']

    def __init__(self, *args, **kwargs):
        booking_instance = kwargs.pop('booking_instance', None)  # Get the booking instance if provided
        super(FlutterPaymentForm, self).__init__(*args, **kwargs)

        # Set each field to read-only
        for field in self.fields.values():
            field.widget.attrs['readonly'] = 'readonly'  

        # Set the booking field to the booking ID
        if booking_instance:
            self.fields['booking'].initial = booking_instance.id  # Set the initial value to the booking ID