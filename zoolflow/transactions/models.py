import uuid
from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from zoolflow.customers.models import Customer

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
        ERROR = "error", "Error"
        VOIDED = "voided", "Voided"
        AUTHORIZED = "authorized", "Authorized"

    ALLOWED_STATE_TRANSITIONS = {
        TransactionState.INITIATED: {
            TransactionState.PENDING,
            TransactionState.FAILED,
            TransactionState.ERROR,
        },
        TransactionState.PENDING: {
            TransactionState.SUCCEEDED,
            TransactionState.FAILED,
            TransactionState.ERROR,
            TransactionState.AUTHORIZED,
        },
        TransactionState.AUTHORIZED: {
            TransactionState.SUCCEEDED,
            TransactionState.FAILED,
            TransactionState.REFUNDED,
            TransactionState.VOIDED,
        },
        TransactionState.SUCCEEDED: {
            TransactionState.REFUNDED,
            TransactionState.VOIDED,
        },
        TransactionState.FAILED: set(),
        TransactionState.ERROR: set(),
        TransactionState.REFUNDED: set(),
        TransactionState.VOIDED: set(),
    }

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
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    transaction_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    order_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    payment_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.merchant_order_id} ({self.state})"

    def can_transition_to(self, next_state: str) -> bool:
        if self.state == next_state:
            return True
        return next_state in self.ALLOWED_STATE_TRANSITIONS.get(self.state, set())

    def transition_to(self, next_state: str):
        if not self.can_transition_to(next_state):
            raise ValueError(f"invalid transition {self.state} -> {next_state}")
        self.state = next_state

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="uniq_customer_idempotency_key",
            )
        ]
