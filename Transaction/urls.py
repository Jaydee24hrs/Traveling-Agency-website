from django.urls import path
from . import views

urlpatterns = [
    # path('transactions/new/', views.create_transaction, name='create_transaction'),
    path('transactions/<int:transaction_id>/edit/', views.update_transaction, name='update_transaction'),
    path('', views.transactions, name='transactions'),
    path('transactions/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    
    #PAY SMALL SMALL
    path('pay-small-small/', views.pay_small_small_list, name='pay_small_small_list'),
    path('pay-small-small/create', views.pay_small_small_create, name='pay_small_small_create'),
    path('pay-small-small/update/<str:id>/', views.pay_small_small_update, name='pay_small_small_update'),
    path('pay-small-small/delete/<str:id>/', views.pay_small_small_delete, name='pay_small_small_delete'),
    
    #paystack webhook
    path('initialize-payment/', views.initialize_payment, name='initialize_payment'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('paystack-payment-hook/', views.paystack_webhook, name='paystack_webhook'),
    #flutterwave
    path('flutter-payment/form/', views.flutter_payment_form, name='flutter_payment_form'),
    path('flutter-payment/', views.flutter_payment, name='flutter_payment'),
    path("payment-callback/", views.flutter_payment_callback, name="flutterwave_payment_callback"),
    path("flw-payment-webhook/", views.flw_payment_webhook, name="flutterwave_payment_webhook"),
    path('paystack-callback/', views.verify_payment, name='verify_payment'),
    path('test_flutterwave', views.test_flutterwave, name='test_flutterwave'),
    path('manual_payment', views.manual_payment, name='manual_payment'),
]

