from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


class IsOwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.role_management in [
            User.Roles.CUSTOMER,
            User.Roles.STAFF,
        ]

    def has_object_permission(self, request, view, obj):
        if request.user.role_management == User.Roles.CUSTOMER:
            return request.user.customer_profile.id == obj.customer_id
        return True


class IsStaff(BasePermission):
    message = "Staff members only"

    def has_permission(self, request, view):
        return (
            request.user.role_management == User.Roles.STAFF
        ) or request.user.is_staff


class IsCustomer(BasePermission):
    message = "Customer's only!"

    def has_permission(self, request, view):
        return request.user.role_management is User.Roles.CUSTOMER
