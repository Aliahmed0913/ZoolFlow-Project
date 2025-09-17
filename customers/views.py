from django.shortcuts import render
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet
from customers.permissions import IsCustomerOwnership
from customers.models import Customer, Address
from rest_framework.permissions import IsAuthenticated
from customers.serializers import CustomerProfileSerializer, CustomerAddressSerializer
# Create your views here.

class CustomerProfile(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerProfileSerializer
    def get_object(self):
        return Customer.objects.get(user = self.request.user)
    

class CustomerAddress(ModelViewSet):
    permission_classes = [IsAuthenticated,IsCustomerOwnership]
    serializer_class = CustomerAddressSerializer
    def get_queryset(self):
        user = self.request.user
        addresses = Address.objects.filter(customer__user_id = user.id)
        return addresses

