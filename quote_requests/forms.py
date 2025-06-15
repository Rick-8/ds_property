from django import forms
from .models import QuoteRequest

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['name', 'email', 'phone', 'description', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-lg bg-transparent text-gold border-light shadow-sm placeholder-gold',
                'rows': 5,
                'placeholder': 'Describe the job clearly: include measurements, materials, access details, etc.',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'd-none',
                'id': 'id_photo',
            }),
        }
