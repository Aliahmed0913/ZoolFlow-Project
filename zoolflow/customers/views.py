from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import generics as g
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Customer, Address, KnowYourCustomer
from .permissions import IsOwnerOrStaff, IsStaff, IsCustomer
from . import serializers as s

# Create your views here.
User = get_user_model()


class CustomerPermissionMixin:
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]


class CustomerProfileAPIView(CustomerPermissionMixin, g.RetrieveUpdateDestroyAPIView):

    serializer_class = s.CustomerProfileSerializer

    def get_object(self):
        obj = get_object_or_404(Customer, user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj


class CustomerValidQuerySetMixin(CustomerPermissionMixin):
    queryset_model = None

    def _get_customer(self):
        user = self.request.user
        is_staff = user.role_management == User.Roles.STAFF or user.is_staff

        if is_staff:
            customer_id = self.kwargs.get("customer_id")
            if not customer_id:
                return None
            return get_object_or_404(Customer, pk=customer_id)

        return get_object_or_404(Customer, user=user)

    def get_queryset(self):
        assert self.queryset_model is not None, "set queryset_model in subclass view"
        customer = self._get_customer()

        user = self.request.user
        is_staff = user.role_management == User.Roles.STAFF or user.is_staff

        if is_staff and customer is None:
            return self.queryset_model.objects.all()

        return self.queryset_model.objects.filter(customer=customer)


class CustomerAddressViewSet(CustomerValidQuerySetMixin, ModelViewSet):
    serializer_class = s.CustomerAddressSerializer
    queryset_model = Address

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        customer = self._get_customer()
        if customer is not None:
            ctx["customer"] = customer
        return ctx

    def perform_create(self, serializer):
        customer = self._get_customer()
        user = self.request.user
        is_staff = user.role_management == User.Roles.STAFF or user.is_staff

        if is_staff and customer is None:
            raise ValidationError(
                {"customer_id": "Required for staff when creating an address."}
            )

        serializer.save(customer=customer)


class KnowYourCustomerListAPIView(CustomerValidQuerySetMixin, g.ListAPIView):
    serializer_class = s.KnowYourCustomerSerializer
    queryset_model = KnowYourCustomer


class KnowYourCustomerStaffDetailAPIView(g.RetrieveUpdateAPIView):
    permission_classes = [IsStaff]
    serializer_class = s.KnowYourCustomerSerializer

    def get_object(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(KnowYourCustomer, pk=pk)


class KnowYourCustomerDetailAPIView(KnowYourCustomerStaffDetailAPIView):
    permission_classes = [IsCustomer]

    def get_object(self):
        return get_object_or_404(KnowYourCustomer, customer__user=self.request.user)


class DownloadKnowYourCustomerAPIView(CustomerPermissionMixin, APIView):

    def get_object(self):
        user = self.request.user
        if user.role_management == User.Roles.STAFF or user.is_staff:
            pk = self.kwargs.get("pk")
            obj = get_object_or_404(KnowYourCustomer, pk=pk)
        else:
            obj = get_object_or_404(KnowYourCustomer, customer__user=self.request.user)

        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk):
        kyc = self.get_object()

        if not kyc.document_file:
            return Response(
                {"detail": "No document uploaded"}, status=status.HTTP_404_NOT_FOUND
            )

        storage = kyc.document_file.storage
        signed_url = storage.url(kyc.document_file.name, expire=60)
        return Response({"url": f"{signed_url}"}, status=status.HTTP_200_OK)
