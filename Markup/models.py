from django.db import models
from django.core.exceptions import ValidationError


class MarkupRuleTyktt(models.Model):
    MARKUP_TYPE_CHOICES = [
        ('discount', 'Discount'),
        ('markup', 'Markup'),
        ('service_fee', 'Service Fee'),
        ('promotional_discount', 'Promotional Discount'),
    ]

    ACCOUNT_TYPE_CHOICES = [
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
    ]

    APPLY_MARKUP_AT_CHOICES = [
        ('booking', 'Booking'),
        ('exchange', 'Exchange'),
        ('refund', 'Refund'),
    ]

    FARE_TYPE_CHOICES = [
        ('corporate', 'Corporate'),
        ('published', 'Published'),
        ('negotiated', 'Negotiated'),
    ]

    PASSENGER_TYPE_CHOICES = [
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('infant', 'Infant'),
    ]

    JOURNEY_TYPE_CHOICES = [
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
        ('multi_city', 'Multi City'),
    ]

    AIR_PROVIDERS_CHOICES = [
        ('amadeus', 'Amadeus'),
        ('galileo', 'Galileo'),
        ('verteil', 'Verteil'),
    ]

    CODE_SHARE_CHOICES = [
        ('emos', 'Equal Marketing and Operating System'),
        ('dmos', 'Different Marketing and Operating System'),
    ]

    CABIN_CLASS_CHOICES = [
        ('Economy', 'Economy'),
        ('Business', 'Business'),
        ('Premium', 'Premium'),
        ('First', 'First'),
    ]

    CURRENCY_CHOICES = [
        ('NGN', 'NGN'),
        ('USD', 'USD'),
    ]

    # Markup details
    name = models.CharField(max_length=255)
    markup_type = models.CharField(max_length=20, choices=MARKUP_TYPE_CHOICES)
    markup_amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    mark_up_currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default="NGN")
    # Apply Markup
    apply_markup_at = models.TextField(blank=True, null=True)
    fare_type = models.TextField(blank=True, null=True)
    passenger_type = models.TextField(blank=True, null=True)

    # Carrier details
    marketing_carrier = models.TextField(blank=True, null=True)
    operating_carrier = models.TextField(blank=True, null=True)
    validating_carrier = models.TextField(blank=True, null=True)
    affiliate_carrier = models.TextField(blank=True, null=True)
    air_providers = models.TextField(blank=True, null=True)
    code_share_flights_type = models.CharField(max_length=20, blank=True, null=True)

    # Fare and journey details
    fare_basis_code = models.TextField(blank=True, null=True)
    office_id = models.TextField(blank=True, null=True)
    journey_type = models.TextField(blank=True, null=True)
    cabin_classes = models.TextField(blank=True, null=True)
    booking_class_of_service = models.TextField(blank=True, null=True)

    # Location details
    from_country = models.TextField(blank=True, null=True)
    from_city = models.TextField(blank=True, null=True)
    to_country = models.TextField(blank=True, null=True)
    to_city = models.TextField(blank=True, null=True)

    # Date filters
    departure_date_after = models.DateField(blank=True, null=True)
    departure_date_between_start = models.DateField(blank=True, null=True)
    departure_date_between_end = models.DateField(blank=True, null=True)
    booking_date_between_start = models.DateField(blank=True, null=True)
    booking_date_between_end = models.DateField(blank=True, null=True)

    # Exclusion rules
    # This will be a list of carrier
    exclude_marketing_carrier = models.TextField(blank=True, null=True)
    exclude_operating_carrier = models.TextField(blank=True, null=True)
    exclude_validating_carrier = models.TextField(blank=True, null=True)
    exclude_affiliate_carrier = models.TextField(blank=True, null=True)
    exclude_booking_classes = models.TextField(blank=True, null=True)
    exclude_booking_class_of_service = models.CharField(max_length=225, blank=True, null=True)
    exclude_fare_basis_code = models.CharField(max_length=225, blank=True, null=True)
    exclude_from_country = models.TextField(blank=True, null=True)
    exclude_from_city = models.TextField(blank=True, null=True)
    exclude_to_country = models.TextField(blank=True, null=True)
    exclude_to_city = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TykttMarkUp(models.Model):
    is_marketing_carrier = models.BooleanField(default=False)
    marketing_carrier = models.CharField(max_length=255, blank=True, null=True)
    is_operating_carrier = models.BooleanField(default=False)
    operating_carrier = models.CharField(max_length=255, blank=True, null=True)
    is_others = models.BooleanField(default=False)
    others = models.CharField(max_length=255, blank=True, null=True)
    office_id = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    corporate_code = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        # Ensure that at least one condition is met
        if not self.marketing_carrier and not self.is_others:
            raise ValidationError("At least one of 'marketing_carrier' or 'is_operating_carrier' must be provided.")
        if self.is_others:
            existing_others = TykttMarkUp.objects.filter(is_others=True).exclude(pk=self.pk)
            if existing_others.exists():
                raise ValidationError("Only one record can have 'is_others=True'.")
    def save(self, *args, **kwargs):
        # Ensure clean is called before saving
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if not self.marketing_carrier or self.marketing_carrier.lower() == "none":
            return "Others"
        return self.marketing_carrier or "Others"


class TykttMarkupCommission(models.Model):
    MARKUP_TYPE_CHOICES = (
        ('Markup', 'Markup'),
        ('Commission', 'Commission'),
    )
    AMOUNT_CHOICES = (
        ('Percentage', 'Percentage'),
        ('Fixed', 'Fixed')
    )
    DA_TYPES = (
        ('Country', 'Country'),
        ('City', 'City'),
    )
    markup_commission = models.CharField(max_length=255, blank=True, null=True, choices=MARKUP_TYPE_CHOICES)
    carbin_class = models.CharField(max_length=255, blank=True, null=True)
    passenger = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_type = models.CharField(max_length=255, blank=True, null=True, choices=AMOUNT_CHOICES, default="Fixed")
    departure = models.CharField(max_length=255, blank=True, null=True)
    departure_type = models.CharField(max_length=255, blank=True, null=True, choices=DA_TYPES)
    arrival = models.CharField(max_length=255, blank=True, null=True)
    operating_carrier = models.CharField(max_length=255, blank=True, null=True)
    validating_carrier = models.CharField(max_length=255, blank=True, null=True)
    office_id = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    fare_type = models.CharField(max_length=255, blank=True, null=True)

    # corporate_code = models.CharField(max_length=255, blank=True, null=True)
    arrival_type = models.CharField(max_length=255, blank=True, null=True, choices=DA_TYPES)
    markup = models.ForeignKey(TykttMarkUp, on_delete=models.CASCADE, related_name='tyktt_commission')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Convert specified fields to uppercase
        if self.departure:
            self.departure = self.departure.upper()
        if self.arrival:
            self.arrival = self.arrival.upper()
        if self.operating_carrier:
            self.operating_carrier = self.operating_carrier.upper()
        if self.office_id:
            self.office_id = self.office_id.upper()
        if self.currency:
            self.currency = self.currency.upper()
        if self.validating_carrier:
            self.validating_carrier = self.validating_carrier.upper()
        super().save(*args, **kwargs)  # Call the parent class's save method

    def __str__(self):
        return f"{self.markup_commission} - {self.amount} {self.currency}"


class ExchangeRate(models.Model):
    rate = models.DecimalField(max_digits=20, decimal_places=9)  # Exchange rate value
    date = models.DateField(auto_now=True)  # Date of the exchange rate
    office_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=225, null=True, blank=True, unique=True)
    marketing_carrier =  models.CharField(max_length=225, null=True, blank=True)
    status = models.BooleanField(default=False)

    class Meta:
        # unique_together = ('from_currency', 'to_currency', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"1 {self.rate} {self.currency} on {self.date}"
    

class ExchangeRateExclution(models.Model):
    # rate = models.DecimalField(max_digits=20, decimal_places=9)  # Exchange rate value
    date = models.DateField(auto_now=True)  # Date of the exchange rate
    office_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=225, null=True, blank=True, unique=True)
    marketing_carrier =  models.CharField(max_length=225, null=True, blank=True)
    status = models.BooleanField(default=False)

    class Meta:
        # unique_together = ('from_currency', 'to_currency', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"1 {self.office_id} {self.currency} on {self.date}"

