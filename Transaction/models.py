# from sys import last_exc
from locale import currency
from uuid import uuid4
from django.db import models




# Create your models here.
class Transaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Card', 'Card'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash', 'Cash'),
        ('Wallet', 'Wallet'),
        # Add other payment methods as needed
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Reversed', 'Reversed'),
    ]

    REMARKS_CHOICES = [
        ('issuance', 'issuance'),
        ('exchange', 'exchange'),
        ('refund', 'refund'),
        ('void', 'void')
    ]

    transaction_date = models.DateField()
    booking_id = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=50, decimal_places=2)
    remark = models.CharField(max_length=20, blank=True, null=True, choices=REMARKS_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    currency = models.CharField(max_length=10, null=True, blank=True)

    # class Meta:
    #     permissions = (
    #         ("tyktt_view_transactions", "User can view Transaction"),
    #         ("tyktt_create_transactions", "User can create and update Transaction"),
    #         ("tyktt_delete_transactions", "User can delete Transaction"),
    #
    #         ("affiliate_view_transaction", "User can  view Transaction"),
    #     )
    def __str__(self):
        return f'{self.booking_id} - {self.amount}'
    
class Pay_small_small(models.Model):
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    payment_plan = models.CharField(max_length=50, blank=True)
    amount = models.DecimalField(max_digits=50, decimal_places=2, blank=True)
    balance = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    paid = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True, default=0.00)
    date_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True)
    currency = models.CharField(max_length=15, default='NGN')
    due_date = models.DateField(null=True, blank=True)
    booking = models.ForeignKey("Booking.Booking", blank=True, null=True, on_delete=models.SET_NULL)
    paystack = models.ForeignKey("Transaction.PayStackTransaction", blank=True, null=True, on_delete=models.SET_NULL)
    flutterwave = models.ForeignKey("Transaction.FlutterwaveTransaction", blank=True, null=True, on_delete=models.SET_NULL)
    class Meta:

        verbose_name_plural = 'Pay small small'
    
    def __str__(self):
        return f'{self.id} - {self.booking}'
    
    def get_manual_payment(self):
        manual_payment = self.manualpayment_set.first()
        if manual_payment and manual_payment.amount:
            return manual_payment
        return self.paid
class PayStackTransaction(models.Model):
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Reversed', 'Reversed'),
    ]
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    email = models.EmailField(max_length=100, blank=True, null=True)
    access_code = models.CharField(max_length=50, blank=True, null=True)
    reference = models.CharField(max_length=50, blank=True, null=True, unique=True)
    amount = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=15, default='NGN')
    time_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=100,choices=STATUS_CHOICES, default="Pending")
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    # status = models.CharField(default="pending", max_length=100)
    booking = models.ForeignKey("Booking.Booking", blank=True, null=True,
                                on_delete=models.SET_NULL, related_name="booking_transaction_id")
    used = models.BooleanField(default=False)
    
    class Meta:

        verbose_name_plural = 'PayStack Transactions'
    
    def __str__(self) -> str:
        return f'{self.email} {self.booking}'
    
   


class FlutterwaveTransaction(models.Model):
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    tx_ref = models.CharField(max_length=100, unique=True)
    flw_ref = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, default='pending')
    payment_type = models.CharField(max_length=50, null=True, blank=True)
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    app_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    merchant_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    processor_response = models.CharField(max_length=100, null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking = models.ForeignKey("Booking.Booking", blank=True, null=True,
                                on_delete=models.SET_NULL, related_name="booking_flutter_transaction_id")
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Flutterwave Transactions'
    
    def __str__(self):
        return f'{self.email} {self.amount}'

class ManualPayment(models.Model):
    booking = models.ForeignKey("Booking.Booking", blank=True, null=True,
                                on_delete=models.SET_NULL, related_name="booking_manual_transaction")
    amount = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_payment = models.DateTimeField()
    currency = models.CharField(max_length=15, default='NGN')
    Pay_small_small = models.ForeignKey("Transaction.Pay_small_small", blank=True, null=True, on_delete=models.SET_NULL, related_name="manual_payments")
    
    
    def __str__(self):
        return f'Manual Payment of {self.amount} for {self.Pay_small_small} with booking id {self.booking}'