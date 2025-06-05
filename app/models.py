from django.db import models
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.core.validators import EmailValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    email=models.EmailField(unique=True,default='example@example.com')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
      


    def __str__(self):
        return self.user.username

