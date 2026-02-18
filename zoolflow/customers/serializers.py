from pathlib import Path
from rest_framework import serializers
from .services.normalizers import normalize_phone_number
from .models import Customer, Address, KnowYourCustomer
from config.settings import DOCUMENT_SIZE, ADDRESSES_COUNT, STATE_LENGTH
from django.db import transaction
import logging

logger = logging.getLogger()


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "user",
            "first_name",
            "last_name",
            "phone_number",
            "dob",
            "is_verified",
        ]
        read_only_fields = ["is_verified", "user"]
        extra_kwargs = {
            f: {"required": True}
            for f in ("first_name", "last_name", "phone_number", "dob")
        }

        def validate_phone_number(value: str):
            return normalize_phone_number(value=value)


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "customer",
            "country",
            "state",
            "city",
            "line",
            "building_number",
            "apartment_number",
            "postal_code",
            "main_address",
        ]
        read_only_fields = ["id", "customer"]
        extra_kwargs = {
            f: {"required": True}
            for f in (
                "state",
                "city",
                "line",
                "building_number",
                "apartment_number",
                "postal_code",
            )
        } | {"main_address": {"default": True}}

    def validate(self, attrs):
        customer = self.context["request"].user.customer_profile
        # on create only
        if not self.instance:
            # check if there is more than the allowed addresses per a customer
            addresses = Address.objects.filter(customer=customer)
            if addresses.count() >= ADDRESSES_COUNT:
                raise serializers.ValidationError(
                    f"Allowed only {ADDRESSES_COUNT} addresses"
                )
        return attrs

    def validate_main_address(self, value):
        if not value:
            # check if there is no current main address
            customer = self.context["request"].user.customer_profile
            main_address = Address.objects.filter(customer=customer, main_address=True)
            # for update exclude the current instance
            if self.instance:
                main_address = main_address.exclude(pk=self.instance.pk)
            if not main_address.exists():
                raise serializers.ValidationError("Must be at least one main address")
        return value

    def validate_state(self, value):
        # must be more than STATE_LENGTH characters
        if len(value) <= STATE_LENGTH:
            logger.warning(
                f"State length must be equal to or more than {STATE_LENGTH} characters"
            )
            raise serializers.ValidationError(
                f"Must be more than {STATE_LENGTH} characters"
            )
        return value

    def update(self, instance, validated_data):
        with transaction.atomic():
            wants_main = validated_data.get("main_address", instance.main_address)

            # prevent DB constraint failure on save when switching to main
            if "main_address" in validated_data and validated_data["main_address"]:
                validated_data["main_address"] = False

            address = super().update(instance, validated_data)

            if wants_main:
                address.set_main_address()

            return address

    def create(self, validated_data):
        with transaction.atomic():
            main_desire = validated_data.get("main_address", True)

            # avoid hitting UniqueConstraint on insert
            if main_desire:
                validated_data["main_address"] = False

            address = super().create(validated_data)

            if main_desire:
                address.set_main_address()

            return address


class KnowYourCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowYourCustomer
        fields = ["customer_id", "document_type", "document_id", "document_file"]
        read_only_fields = ("customer_id",)
        extra_kwargs = {
            f: {"required": True}
            for f in ("document_type", "document_id", "document_file")
        }

    def validate_document_file(self, value):
        # uploaded document size must be less than 250 KB
        if value.size > DOCUMENT_SIZE:
            logger.warning("File size is too big")
            raise serializers.ValidationError(
                detail=f"file too large. max size {DOCUMENT_SIZE}KB"
            )

        # check that the uploaded file with types pdf/jpg
        extension = Path(value.name).suffix.lower()
        if extension not in [".pdf", ".jpg"]:
            logger.warning("File type isn't supported")
            raise serializers.ValidationError(detail="file must be an pdf/jpg type")

        return value
