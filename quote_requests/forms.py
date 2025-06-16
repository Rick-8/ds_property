from django import forms
from .models import QuoteRequest
from accounts.models import Property

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = [
            'name', 'email', 'phone', 'description', 'photo', 'related_property',
            'address_line1', 'address_line2', 'city', 'state', 'postcode',
        ]
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['related_property'].queryset = Property.objects.filter(profile=user.profile)
            self.fields['address_line1'].widget = forms.HiddenInput()
            self.fields['address_line2'].widget = forms.HiddenInput()
            self.fields['city'].widget = forms.HiddenInput()
            self.fields['state'].widget = forms.HiddenInput()
            self.fields['postcode'].widget = forms.HiddenInput()
        else:
            self.fields['related_property'].widget = forms.HiddenInput()
            self.fields['address_line1'].widget.attrs['placeholder'] = 'Street address or building'
            self.fields['address_line2'].widget.attrs['placeholder'] = 'Apartment, suite, unit, etc. (optional)'
            self.fields['city'].widget.attrs['placeholder'] = 'City'
            self.fields['state'].widget.attrs['placeholder'] = 'State'
            self.fields['postcode'].widget.attrs['placeholder'] = 'Postcode'
