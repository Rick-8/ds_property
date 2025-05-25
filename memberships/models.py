from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from accounts.models import Property


CATEGORY_CHOICES = [
    ('B2B', 'Border 2 Border'),
    ('SZP', 'Splash Zone Pools'),
    ('DSP', 'DS Property Management'),
]

TIER_CHOICES = [
    ('SINGLE', 'Single'),
    ('DOUBLE', 'Double'),
]


class ServicePackage(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    description = RichTextField()
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_category_display()} {self.get_tier_display()}"


class ServiceAgreement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_package = models.ForeignKey('ServicePackage', on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def billing_address(self):
        profile = self.user.profile
        return {
            'address_line_1': profile.default_address_line_1,
            'address_line_2': profile.default_address_line_2,
            'city': profile.default_city,
            'postcode': profile.default_postcode,
            'country': profile.default_country,
        }

    def __str__(self):
        return f"{self.user.username} - {self.service_package} @ {self.property.label}"
