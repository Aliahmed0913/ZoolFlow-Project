from rest_framework.permissions import BasePermission


class IsVerifiedCustomer(BasePermission):
    """
    Custom permission to only allow verified customers to create transactions.
    """

    message = "Customer_profile isn't existing or not verified."

    def has_permission(self, request, view):
        if request.method != "GET":
            is_customer = hasattr(request.user, "customer_profile")
            if not is_customer:
                return False
            return (
                request.user.is_authenticated
                and request.user.customer_profile.is_verified
            )
        return True
