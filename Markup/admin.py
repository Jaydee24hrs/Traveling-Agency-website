from django.contrib import admin
from .models import MarkupRuleTyktt, TykttMarkUp, TykttMarkupCommission

# Register your models here.
admin.site.register(MarkupRuleTyktt)
admin.site.register(TykttMarkUp)
admin.site.register(TykttMarkupCommission)
