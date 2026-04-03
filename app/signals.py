from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import send_welcome_email  # or wherever your email function is
from .models import UserProfile

@receiver(post_save, sender=User)
def send_email_on_signup(sender, instance, created, **kwargs):
    if created:
        send_welcome_email(instance.email, instance.username)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"email": instance.email or "example@example.com"},
        )


@receiver(post_save, sender=User)
def sync_user_profile_email(sender, instance, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(
        user=instance,
        defaults={"email": instance.email or "example@example.com"},
    )
    if instance.email and profile.email != instance.email:
        profile.email = instance.email
        profile.save(update_fields=["email"])
