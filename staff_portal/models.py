from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Property
from memberships.models import ServiceAgreement

User = get_user_model()

JOB_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
    ('MISSED', 'Missed'),
]

class Route(models.Model):
    name = models.CharField(max_length=100, unique=True)
    staff = models.ManyToManyField(User, related_name='routes', blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    service_agreement = models.ForeignKey(ServiceAgreement, on_delete=models.SET_NULL, null=True, blank=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_staff = models.ManyToManyField(User, related_name='assigned_jobs', blank=True)

    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)

    staff_feedback = models.TextField(blank=True, help_text="Optional notes staff leave after completing the job")
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.title} @ {self.property.label} on {self.scheduled_date}"


class JobPhoto(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='job_photos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.job.title} by {self.uploaded_by}"
