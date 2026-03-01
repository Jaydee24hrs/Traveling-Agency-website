from django.contrib import admin
from .models import CustomUser, OTP, Customer

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(OTP)
admin.site.register(Customer)
