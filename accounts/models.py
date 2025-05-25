from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import pytz


class Profile(models.Model):
    USER_TYPES = [
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    ACCOUNT_STATUSES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)

    default_address_line_1 = models.CharField(max_length=255, blank=True)
    default_address_line_2 = models.CharField(max_length=255, blank=True)
    default_city = models.CharField(max_length=100, blank=True)
    default_postcode = models.CharField(max_length=20, blank=True)
    default_country = models.CharField(max_length=100, blank=True)

    preferred_contact_time = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=100, choices=[(tz, tz) for tz in pytz.all_timezones], default='UTC')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUSES, default='active')

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    notes = RichTextField(blank=True, null=True)

    profile_completed = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Property(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='properties')

    label = models.CharField(max_length=100, help_text="e.g. Home, Rental 1")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='UK')
    notes = RichTextField(blank=True, null=True)
    route_number = models.PositiveIntegerField(null=True, blank=True, help_text="Route number for staff")

    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    has_active_service = models.BooleanField(default=False, help_text="Does this property currently have an active service plan?")

    @property
    def address_summary(self):
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.extend([self.city, self.postcode, self.country])

        return ', '.join(filter(None, parts))

    def __str__(self):
        return f"{self.label} - {self.address_line_1}"

    class Meta:
        verbose_name_plural = "Properties"
