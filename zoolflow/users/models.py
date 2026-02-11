from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

# Create your models here.


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role_management", User.Roles.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "admin"
        STAFF = "STAFF", "staff"
        CUSTOMER = "CUSTOMER", "customer"

    role_management = models.CharField(
        max_length=10, choices=Roles.choices, default=Roles.CUSTOMER
    )
    email = models.EmailField(unique=True)
    objects = CustomUserManager()

    def __str__(self):
        return self.username
