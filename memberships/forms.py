from django import forms
from .models import ServicePackage


class ServicePackageForm(forms.ModelForm):
    class Meta:
        model = ServicePackage
        fields = ['name', 'category', 'tier', 'description', 'price_usd', 'is_active']
