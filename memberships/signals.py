from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from webpush import send_user_notification
from .models import ServiceAgreement


@receiver(post_save, sender=ServiceAgreement)
def notify_superusers_on_subscription(sender, instance, created, **kwargs):
    if created:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        payload = {
            "head": "New Subscription Created",
            "body": f"A new subscription for {instance.service_package.name} was created.",
            "url": "/admin/memberships/subscription/"
        }

        for user in UserModel.objects.filter(is_superuser=True):
            send_user_notification(user=user, payload=payload, ttl=1000)
