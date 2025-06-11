# quote_requests/forms.py

from django import forms
from .models import QuoteRequest


class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['name', 'email', 'phone', 'description', 'photo']


class QuoteFeedbackForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['feedback']
        widgets = {'feedback': forms.Textarea(attrs={'rows': 4})}
