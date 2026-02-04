import hashlib
import logging
from django.conf import settings
from zoolflow.transactions.services.webhook import WebhookService

logger = logging.getLogger(__name__)


def verify_mailgun_hmac(payload):
    """
    calculate an HMAC from webhook payload and compare with received signature
    """
    token = payload.get("token")
    timestamp = payload.get("timestamp")
    received_hmac = payload.get("signature")
    concatenated_fields = f"{timestamp}{token}"
    secret_key = getattr(settings, "MAILGUN_WEBHOOK_SIGINING_KEY")

    WebhookService.verify_signature(
        received_hmac=received_hmac,
        concatenated_fields=concatenated_fields,
        secret_key=secret_key,
        digestmod=hashlib.sha256,
    )
