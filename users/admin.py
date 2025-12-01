from django.contrib import admin
from users.models import User
from django.contrib.auth.admin import UserAdmin
from users.forms import CustomUserChangeForm,CustomUserCreationForm
# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    add_fieldsets = (
        (None,{'classes':('wide',),
            "fields": ("username", "email", "role_management", "password1", "password2"),
        }),
    )
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role info',{"fields": ("role_management",)}),
    )

    list_display = ("id", "username", "email", "role_management", "is_staff", "is_superuser")
    list_filter = ("role_management", "is_staff", "is_superuser")
    search_fields = ("username", "email")
