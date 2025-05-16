from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


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
