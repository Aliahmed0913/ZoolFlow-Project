import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from customers.models import Customer

# Create your models here.


def dufault_merchant_order_id():
    return "ORD-" + str(uuid.uuid4())


class Transaction(models.Model):
    class SupportedPaymentProviders(models.TextChoices):
        PAYMOB = "PayMob", "PayMob"

    class TransactionState(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="customer_transaction"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_provider = models.CharField(
        max_length=50,
        choices=SupportedPaymentProviders.choices,
        default=SupportedPaymentProviders.PAYMOB,
    )
    state = models.CharField(
        max_length=20,
        editable=False,
        choices=TransactionState.choices,
        default=TransactionState.INITIATED,
    )
    merchant_order_id = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        default=dufault_merchant_order_id,
    )
    transaction_id = models.CharField(
        max_length=64, db_index=True, null=True, blank=True
    )
    order_id = models.CharField(max_length=200, null=True, blank=True)
    payment_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.merchant_order_id} ({self.state})"

    class Meta:
        ordering = ["-created_at"]
