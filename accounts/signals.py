from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib import messages


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create profile with email synced
        Profile.objects.create(user=instance, email=instance.email)
    else:
        # Update profile email if User email changed
        profile = getattr(instance, 'profile', None)
        if profile and profile.email != instance.email:
            profile.email = instance.email
            profile.save()


def clear_auth_messages(sender, request, **kwargs):
    storage = messages.get_messages(request)
    # Clear messages added by allauth login/logout by filtering them out
    storage.used = True


user_logged_in.connect(clear_auth_messages)
user_logged_out.connect(clear_auth_messages)
