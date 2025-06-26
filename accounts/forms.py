from django import forms
from .models import Profile, Property
from allauth.account.forms import SignupForm


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email')

    # Checkbox to optionally add the default address as a saved property
    add_as_property = forms.BooleanField(
        required=False,
        label="Add this address to my property list",
        help_text="Check this if you'd like to save this address as a service property"
    )

    class Meta:
        model = Profile
        fields = [
            'email', 'phone', 'company_name', 'vat_number',
            'default_address_line_1', 'default_address_line_2',
            'default_city', 'default_postcode', 'default_country',
            'preferred_contact_time', 'timezone', 'notes',
            'marketing_consent',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Sync email with User model
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.save()
        profile.email = self.cleaned_data['email']

        if commit:
            profile.save()

            # Handle the "add as property" checkbox
            if self.cleaned_data.get('add_as_property'):
                address_exists = Property.objects.filter(
                    profile=profile,
                    address_line_1=profile.default_address_line_1,
                    postcode=profile.default_postcode,
                    city=profile.default_city,
                    country=profile.default_country,
                ).exists()

                if not address_exists:
                    Property.objects.create(
                        profile=profile,
                        label="Default Address",
                        address_line_1=profile.default_address_line_1,
                        address_line_2=profile.default_address_line_2,
                        city=profile.default_city,
                        postcode=profile.default_postcode,
                        country=profile.default_country,
                    )

        return profile


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['profile', 'date_added', 'route_number', 'has_active_service', 'stripe_subscription_id']


class CustomSignupForm(SignupForm):
    marketing_consent = forms.BooleanField(
        required=False,
        label="I would like to receive news, offers, and updates by email from DS Property Maintenance."
    )

    def save(self, request):
        user = super().save(request)
        # Save marketing consent to the user's profile
        profile = getattr(user, 'profile', None)
        if profile:
            profile.marketing_consent = self.cleaned_data.get('marketing_consent', False)
            profile.save()
        return user