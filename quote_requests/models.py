# quote_requests/models.py

from django.db import models
from django.conf import settings
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

    def __str__(self):
        return f"{self.name} - {self.email} ({self.status})"
