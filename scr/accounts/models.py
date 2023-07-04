from django.contrib.auth.models import AbstractUser
from django.db import models


class Shopper(AbstractUser):
    address = models.CharField(max_length=300, blank=True)
    address_detail = models.CharField(max_length=300, blank=True)
    zip_code = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=300, blank=True)
    country = models.CharField(max_length=300, blank=True)
    phone_number = models.IntegerField(blank=True, unique=True, null=True)
