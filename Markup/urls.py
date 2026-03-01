from django.urls import path
from . import views

urlpatterns = [
    # MarkupRuleTyktt URLs
    path('markup_rule_tyktt/', views.markup_rule_tyktt_list, name='markup_rule_tyktt_list'),
    path('markup_rule_tyktt/create/', views.markup_rule_tyktt_create, name='markup_rule_tyktt_create'),
    path('markup_rule_tyktt/update/<int:pk>/', views.markup_rule_tyktt_update, name='markup_rule_tyktt_update'),
    path('update_markup_rule/update/<int:pk>/', views.update_markup_rule, name='update_markup_rule'),
    path('markup_rule_tyktt/delete/<int:pk>/', views.markup_rule_tyktt_delete, name='markup_rule_tyktt_delete'),

    # Duplicate Markup
    path('duplicate_markup/<int:pk>/', views.duplicate_markup_rule, name='duplicate_markup_rule'),

    # Flight Markup Search
    path('flight_search_markup/', views.flight_search_markup, name='flight_search_markup'),

    path('markups/create/', views.markup_create, name='markup_create'),
    path('markups/update/<int:pk>/', views.markup_update, name='markup_update'),
    path('markups_status/update/<int:pk>/', views.update_tyktt_markup_rule, name='update_tyktt_markup_rule'),
    path('markups/delete/<int:pk>/', views.markup_delete, name='markup_delete'),
    path('markups_commission/delete/<int:pk>/', views.markup_commission_delete, name='markup_commission_delete'),

     # ExchangeRate URLs
    path('exchange_rates/new/', views.exchange_rate_create, name='exchange_rate_create'),
    path('exchange_rates/<int:pk>/edit/', views.exchange_rate_update, name='exchange_rate_update'),
    path('exchange_rates/<int:pk>/edit/status/', views.exchange_rate_update_status, name='exchange_rate_update_status'),
    path('exchange_rates/<int:pk>/delete/', views.exchange_rate_delete, name='exchange_rate_delete'),

    path('exchange_rate_exclutions/new/', views.exchange_rate_exclution_create, name='exchange_rate_exclution_create'),
    path('exchange_rate_exclutions/<int:pk>/edit/', views.exchange_rate_exclution_update, name='exchange_rate_exclution_update'),
    path('exchange_rate_exclutions/<int:pk>/edit/status', views.exchange_rate_exclution_update_status, name='exchange_rate_exclution_update_status'),
    path('exchange_rate_exclutions/<int:pk>/delete/', views.exchange_rate_exclution_delete, name='exchange_rate_exclution_delete'),

    path('markup_delete_corporatecode/', views.markup_delete_corporatecode, name='markup_delete_corporatecode'),
]
