from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


class IsCustomer(BasePermission):
    message = "Customers only!"

    def has_permission(self, request, view):
        return request.user.role_management == User.Roles.CUSTOMER
