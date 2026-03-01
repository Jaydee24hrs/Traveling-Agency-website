from django.contrib import admin
from .models import Booking, Passenger, Itinerary



class BookingAdmin(admin.ModelAdmin):
    model=Booking
    list_display = ('pnr', 'booking_date', 'office_id', 'amount', 'converted_amount', 'status')
    list_filter = ('status', 'booking_date')
    search_fields = ('pnr', 'booking_id', 'office_id')
    ordering = ('-booking_date',)
    
# Register your models here.
admin.site.register(Booking, BookingAdmin)
admin.site.register(Passenger)
admin.site.register(Itinerary)  