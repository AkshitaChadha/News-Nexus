from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import send_welcome_email  # or wherever your email function is

@receiver(post_save, sender=User)
def send_email_on_signup(sender, instance, created, **kwargs):
    if created:
        
        send_welcome_email(instance.email, instance.username)
