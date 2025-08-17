from users.models import User
from rest_framework.permissions import BasePermission


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role_management == 'ADMIN':
            return True
        return obj.id == request.user.id

        