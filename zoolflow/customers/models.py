from django.db import models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
from . import validators as V
from config.settings import ADDRESSES_COUNT

# Create your models here.
User = get_user_model()


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_profile"
    )

    first_name = models.CharField(
        max_length=50,
        blank=True,
        validators=[V.validate_first_name],
        help_text="Name must match the name in the document to succeed validation",
    )
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[V.validate_phone_number],
    )
    dob = models.DateField(null=True, blank=True, validators=[V.valid_age])
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name or self.user.username


class Address(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    country = CountryField(default="EG", editable=False)
    line = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(
        max_length=10, blank=True, validators=[V.EGYPT_POSTAL_REGX]
    )

    building_number = models.CharField(max_length=10, blank=True)
    apartment_number = models.CharField(max_length=10, blank=True)
    main_address = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_main_address(self):
        # lock the customer row
        self.customer.__class__.objects.select_for_update().filter(
            pk=self.customer.id
        ).get()
        # disable other main addresses
        type(self).objects.filter(customer=self.customer, main_address=True).exclude(
            pk=self.pk
        ).update(main_address=False)
        if not self.main_address:
            self.main_address = True
            self.save(update_fields=["main_address"])

    class Meta:
        ordering = ["-main_address", "-updated_at"]
        constraints = [
            UniqueConstraint(
                fields=("customer",),
                condition=Q(main_address=True),
                name="single_main_address_for_a_customer",
                violation_error_message="only one main address can be",
            )
        ]

    def __str__(self):
        return f"{self.customer.first_name or self.customer.user.username} - {self.country}"


class KnowYourCustomer(models.Model):
    class DocumentType(models.TextChoices):
        NATIONAL_ID = "national_id", "National_id"
        PASSPORT = "passport", "Passport"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="kyc"
    )
    document_type = models.CharField(
        max_length=20, choices=DocumentType.choices, default=DocumentType.NATIONAL_ID
    )
    document_id = models.CharField(max_length=100, blank=True)
    document_file = models.FileField(upload_to="kyc-document/", blank=True)
    status_tracking = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer.first_name or self.customer.user.username} - {self.document_type}"
