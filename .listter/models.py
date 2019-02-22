from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    screen_name = models.CharField(max_length=100)
    oauth_token = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
