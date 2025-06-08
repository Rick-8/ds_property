from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib import messages
from webpush import send_user_notification
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, email=instance.email)
    else:
        profile = getattr(instance, 'profile', None)
        if profile and profile.email != instance.email:
            profile.email = instance.email
            profile.save()


def clear_auth_messages(sender, request, **kwargs):
    storage = messages.get_messages(request)
    storage.used = True


@receiver(user_logged_in)
def notify_superuser_on_login(sender, request, user, **kwargs):
    if user.is_staff:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        superusers = UserModel.objects.filter(is_superuser=True)
        payload = {
            "head": "Staff Login",
            "body": f"{user.get_full_name() or user.username} just logged in.",
            "icon": "/static/media/dsproperty-logo-pwa.png",
            "url": "/admin/"
        }
        for superuser in superusers:
            try:
                send_user_notification(user=superuser, payload=payload, ttl=1000)
            except Exception as e:
                print(f"Web push failed: {e}")


user_logged_in.connect(clear_auth_messages)
user_logged_out.connect(clear_auth_messages)
