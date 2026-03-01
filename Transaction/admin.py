from django.contrib import admin
from .models import Pay_small_small, PayStackTransaction, Transaction, FlutterwaveTransaction, ManualPayment


@admin.register(Pay_small_small)
class Pay_small_smallAdmin(admin.ModelAdmin):
    model = Pay_small_small
    list_display = ["booking", 'first_name', 'last_name', 'email', 'phone', 'amount',"paid", "balance", 'time_updated']
    search_fields = ["booking", 'first_name', 'last_name', 'email', 'phone']
    list_filter = ['date_created',"email"]
    ordering = ['-date_created']

@admin.register(PayStackTransaction)
class PayStackTransactionAdmin(admin.ModelAdmin):
    model = PayStackTransaction
    list_display = ["booking", "reference", 'email', 'amount', 'date_created', 'time_updated',"" "status"]
    search_fields = ["booking", 'email', "reference"]
    list_filter = ['date_created']
# Register your models here

@admin.register(FlutterwaveTransaction)
class FlutterWaveTransactionAdmin(admin.ModelAdmin):
    model = FlutterwaveTransaction
    list_display = [ "tx_ref", "flw_ref", 'email', 'amount', 'created_at', 'updated_at', "status"]
    search_fields = ['email', "tx_ref", "flw_ref"]
    list_filter = ['created_at']
    ordering = ['-created_at']


@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    model = ManualPayment
    list_display = ["booking", "amount", "date_payment", "Pay_small_small"]
    search_fields = ["booking"]
    list_filter = ['date_payment']
    ordering = ['-date_payment']
# Register any other models without custom admin settings

admin.site.register(Transaction)