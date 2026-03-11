from django.db import models


# Create your models here.
class EmailEvent(models.Model):
    class EmailEventPurpose(models.TextChoices):
        TRANSACTION_UPDATE = "transaction_update", "Transaction Update"
        VERIFICATION_CODE = "verification_code", "Verification Code"

    class MessageStatus(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        QUEUED = "queued", "Queued"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    idempotent_key = models.CharField(max_length=100, unique=True)
    event_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    provider_response_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )
    to_email = models.CharField(max_length=50)
    purpose = models.CharField(max_length=100, choices=EmailEventPurpose.choices)
    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.INITIATED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.idempotent_key
