import logging
from django.db import transaction
from ..models import EmailEvent
from zoolflow.transactions.services.webhook import WebhookServiceError

logger = logging.getLogger(__name__)


class UpdateEmailEventTracker:
    def when_queued(event: EmailEvent, reponse_message):
        """
        Update EmailEvent when email is queued,
        By adding message id and status recieved from API response
        """
        event.provider_response_id = reponse_message.strip("<>")
        event.status = event.MessageStatus.QUEUED
        event.save(update_fields=["provider_response_id", "status"])

    @staticmethod
    def with_webhook(event_type, message_id, event_id):
        """
        Update EmailEvent status,
        And add event-id for dedupe based on webhook event-data
        """

        with transaction.atomic():
            email_event = EmailEvent.objects.select_for_update().filter(
                provider_response_id=message_id
            )
            if not email_event.exists():
                logger.error(
                    f"EmailEvent with message_id {message_id} does not exist.",
                )
                raise WebhookServiceError(
                    "EmailEvent matching query does not exist.",
                )
            email_event = email_event.first()
            if event_type == "delivered":
                email_event.status = EmailEvent.MessageStatus.DELIVERED
            elif event_type == "failed":
                email_event.status = EmailEvent.MessageStatus.FAILED
            email_event.event_id = event_id
            email_event.save(update_fields=["status", "event_id"])

            key = email_event.idempotent_key
            logger.info(
                f"Mailgun {event_type}-{email_event.purpose} for user with key ({key})."
            )
