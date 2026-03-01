from django import forms
from .models import ExchangeRate, ExchangeRateExclution, MarkupRuleTyktt, TykttMarkUp, TykttMarkupCommission


class MarkupRuleTykttForm(forms.ModelForm):

    class Meta:
        model = MarkupRuleTyktt
        fields = '__all__'



class TykttMarkUpForm(forms.ModelForm):
    class Meta:
        model = TykttMarkUp
        fields = '__all__'


class TykttMarkupCommissionForm(forms.ModelForm):
    class Meta:
        model = TykttMarkupCommission
        fields = '__all__'



class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = '__all__'

class ExchangeRateExclutionForm(forms.ModelForm):
    class Meta:
        model = ExchangeRateExclution
        fields = '__all__'

