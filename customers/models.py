from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
User = get_user_model()

class Customer(models.Model):
    pass
class Addresses(models.Model):
    pass