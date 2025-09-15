from django.shortcuts import render
from rest_framework.generics import UpdateAPIView,RetrieveUpdateAPIView
from rest_framework.response import Response
from customers.models import Customer
from rest_framework.permissions import IsAuthenticated
from core.permissions.user import IsAdminOrOwner
from customers.serializers import CustomerProfileSerializer
# Create your views here.

class CustomerProfile(RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return Customer.objects.get(user = self.request.user)