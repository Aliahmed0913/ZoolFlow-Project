from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Customer, Address, KnowYourCustomer
from .permissions import IsCustomer
from .serializers import (
    CustomerProfileSerializer,
    CustomerAddressSerializer,
    KnowYourCustomerSerializer,
)

# Create your views here.


class CustomerProfileAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        return get_object_or_404(Customer, user=self.request.user)


class CustomerAddressViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = CustomerAddressSerializer

    def perform_create(self, serializer):
        customer = get_object_or_404(Customer, user=self.request.user)
        serializer.save(customer=customer)

    def get_queryset(self):
        addresses = Address.objects.filter(customer__user=self.request.user)
        return addresses


class KnowYourCustomerAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = KnowYourCustomerSerializer

    def get_object(self):
        return get_object_or_404(KnowYourCustomer, customer__user=self.request.user)
