from django.contrib import admin
from users.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.
# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     fieldsets = UserAdmin.fieldsets + (
#         ('Role info',{"fields": ("role_management", "phone_number")}),
#     )
#     add_fieldsets = UserAdmin.add_fieldsets + (
#         ("Role Info", {"fields": ("role_management", "phone_number")}),
#     )
#     list_display = ("id", "username", "email", "role_management", "is_staff", "is_superuser")
#     list_filter = ("role_management", "is_staff", "is_superuser")
#     search_fields = ("username", "email", "phone_number")
