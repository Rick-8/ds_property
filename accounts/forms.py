from django import forms
from .models import Profile, Property


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['user', 'is_verified', 'stripe_customer_id', 'notes', 'date_created' 'profile_image']


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['profile', 'date_added', 'profile_image']
