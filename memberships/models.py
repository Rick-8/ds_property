from django.db import models
from ckeditor.fields import RichTextField


CATEGORY_CHOICES = [
    ('B2B', 'Border 2 Border'),
    ('SPLASH', 'SplashZone Pools'),
]

TIER_CHOICES = [
    ('SILVER', 'Silver'),
    ('GOLD', 'Gold'),
]


class ServicePackage(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    description = RichTextField()
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_category_display()} {self.get_tier_display()}"
