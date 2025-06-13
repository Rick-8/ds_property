# quote_requests/models.py

from django.db import models
from django.conf import settings
from decimal import Decimal
from .storage_backends import QuoteImageStorage


class QuoteRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('PAID', 'Paid'),
        ('LOCKED', 'Locked'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    description = models.TextField()
    photo = models.ImageField(upload_to='requests/', storage=QuoteImageStorage())
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Totals-related fields
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_totals(self):
        subtotal = sum(item.subtotal for item in self.items.all())
        tax = subtotal * (self.tax_percent / Decimal(100))
        total = subtotal + tax

        self.total_subtotal = subtotal
        self.total_tax = tax
        self.total_amount = total
        self.save()

    def __str__(self):
        return f"{self.name} - {self.email} ({self.status})"


class QuoteItem(models.Model):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.description} (x{self.quantity}) - ${self.unit_price}"