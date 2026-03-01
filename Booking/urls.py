from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage, name='manage-booking'),
    path('<int:booking_id>', views.bookinginfo, name='bookinginfo'),
    path('delete/manual-payment/<int:payment_id>/', views.delete_manual_payment, name='delete_manual_payment'),
    path('delete/pay-small-small/<str:paystack_ref>/', views.delete_pay_small_small, name='delete_pay_small_small'),
    path('delete/most-recent-transaction/<int:transaction_id>/', views.delete_most_recent_transaction, name='delete_most_recent_transaction'),
    path('cancel_booking/<int:booking_id>', views.cancel_booking, name='cancel_booking'),
    path('flight_search', views.flight_search, name='flight_search'),
    path('flight_search_v3', views.flight_search_v3, name='flight_search_v3'),
    path('flight_booking', views.flight_booking, name='flight_booking'),
    path('search_flight_code', views.search_flight_code, name='search_flight_code'),
    path('get_city_by_iata_code', views.get_city_by_iata_code, name='get_city_by_iata_code'),
    path('get_fare_rule', views.get_fare_rule, name='get_fare_rule'),
    path('book_flight', views.book_flight, name='book_flight'),
    path('update_book_flight/<int:booking_id>', views.update_booking_info, name='update_book_flight'),
    path('update_booking/<int:booking_id>', views.update_booking, name='update_booking'),
    path('send-pdf-via-email/<int:booking_id>', views.send_pdf_via_email, name='send_pdf_via_email'),
    path('get_airlines/', views.load_airlines, name='get_airlines'),
    path('get_cities/', views.load_cities, name='get_cities'),
    path('get_all_cities/', views.get_cities, name='get_all_cities'),
    path('get_upsell/', views.get_upsell, name='get_upsell'),
]
