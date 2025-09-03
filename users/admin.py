from django.contrib import admin
from users.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass