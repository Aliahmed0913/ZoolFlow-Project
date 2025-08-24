from users.models import User
from rest_framework.permissions import BasePermission


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role_management == 'ADMIN':
            return True
        return obj.id == request.user.id
        
class IsAdmin(BasePermission):
    def has_permission(self, request,view):
        return request.user.is_authenticated and request.user.role_management == "ADMIN"
    
    def has_object_permission(self, request, view, obj):
        if request.user.role_management == 'ADMIN':
            return True
        return False