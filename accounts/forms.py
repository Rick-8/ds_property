from django import forms
from .models import Profile, Property


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email')  # Overrides the one in the model

    class Meta:
        model = Profile
        fields = [
            'email', 'phone', 'company_name', 'vat_number',
            'default_address_line_1', 'default_address_line_2',
            'default_city', 'default_postcode', 'default_country',
            'preferred_contact_time', 'timezone', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.save()
        profile.email = self.cleaned_data['email']
        if commit:
            profile.save()
        return profile


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['profile', 'date_added', 'route_number']
