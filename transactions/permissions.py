from rest_framework.permissions import BasePermission

class IsVerifiedCustomer(BasePermission):
    """
    Custom permission to only allow verified customers to create transactions.
    """
    message = 'Customer profile is not verified.'
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.customer_profile.is_verified  
        return True