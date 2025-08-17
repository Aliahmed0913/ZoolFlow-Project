from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.core.validators import RegexValidator
# Create your models here.

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN='ADMIN','admin'
        STAFF='STAFF','staff'
        CUSTOMER='CUSTOMER','customer'
    role_management=models.CharField(max_length=10, choices=Roles.choices, default=Roles.CUSTOMER)
        
    email=models.EmailField(unique=True)
    password = models.CharField(max_length=128)
   
    phone_number = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.username
    