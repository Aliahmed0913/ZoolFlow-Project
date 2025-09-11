from django.db import models
from django.contrib.auth.models import AbstractUser 
# Create your models here.

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN='ADMIN','admin'
        STAFF='STAFF','staff'
        CUSTOMER='CUSTOMER','customer'
    
    role_management=models.CharField(max_length=10, choices=Roles.choices, default=Roles.CUSTOMER)     
    email=models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.username

class EmailCode(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at =  models.DateTimeField(auto_now_add=True)