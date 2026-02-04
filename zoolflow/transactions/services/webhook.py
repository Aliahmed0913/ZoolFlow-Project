import logging
import hashlib
import hmac
from django.conf import settings
from django.db import transaction as db_transaction
from .helpers import bring_transaction, retrieve_transaction_for_update
from ..models import Transaction as TXN

logger = logging.getLogger(__name__)


class WebhookServiceError(Exception):
    # Raised when Webhook handling fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class WebhookService:
    def __init__(self, data, transaction_id):
        self.data = data
        merchant_id = data.get("order", {}).get("merchant_order_id")
        self.transaction = bring_transaction(merchant_order_id=merchant_id)
        self.transaction_id = transaction_id

    def handle_webhook(self):
        """
        Handle transaction state transition based on webhook received data
        """
        # Extract webhook data that define transaction current situation
        success = self.data.get("success")
        pending = self.data.get("pending")
        is_refunded = self.data.get("is_refunded")
        data_status = self.data.get("data", {})
        message = data_status.get("message", "")
        response_code = data_status.get("acq_response_code", "")

        # Check various scenarios to update transaction state
        # Additional flags used to identify pending state accurately
        is_pending = (
            message
            in [
                "AUTHENTICATION_UNAVAILABLE",
                "AUTHENTICATION_PENDING",
            ]
            and response_code == "PROCEED"
        )
        if is_refunded:
            self._webhook_transition(TXN.TransactionState.REFUNDED)
            return
        elif success:
            self._webhook_transition(TXN.TransactionState.SUCCEEDED)
            return
        elif pending or is_pending:
            self._webhook_transition(TXN.TransactionState.PENDING)
            return
        else:
            self._webhook_transition(TXN.TransactionState.FAILED)
            return

    def _webhook_transition(self, new_state):
        """
        Update the transaction state
        Assign transaction_id based on returned webhook
        """
        from zoolflow.notifications.tasks import transaction_state_email_task

        with db_transaction.atomic():
            tx = retrieve_transaction_for_update(id=self.transaction.id)
            tx.state = new_state
            tx.transaction_id = self.transaction_id
            tx.save(update_fields=["state", "transaction_id"])
            logger.info(f"Transaction {tx.transaction_id} updated to {tx.state}.")
            db_transaction.on_commit(
                lambda: transaction_state_email_task(self.transaction_id)
            )

    def verify_paymob_hmac(self, received_hmac):
        concatenate_fields = str.join(
            "",
            [
                str(self.data["amount_cents"]),
                str(self.data["created_at"]),
                str(self.data["currency"]),
                str(self.data["error_occured"]).lower(),
                str(self.data["has_parent_transaction"]).lower(),
                str(self.data["id"]),
                str(self.data["integration_id"]),
                str(self.data["is_3d_secure"]).lower(),
                str(self.data["is_auth"]).lower(),
                str(self.data["is_capture"]).lower(),
                str(self.data["is_refunded"]).lower(),
                str(self.data["is_standalone_payment"]).lower(),
                str(self.data["is_voided"]).lower(),
                str(self.data["order"]["id"]),
                str(self.data["owner"]),
                str(self.data["pending"]).lower(),
                str(self.data["source_data"]["pan"]),
                str(self.data["source_data"]["sub_type"]),
                str(self.data["source_data"]["type"]),
                str(self.data["success"]).lower(),
            ],
        )
        secret_key = getattr(settings, "HMAC_SECRET_KEY")
        WebhookService.verify_signature(
            received_hmac=received_hmac,
            concatenated_fields=concatenate_fields,
            secret_key=secret_key,
        )
        logger.info(
            f"PayMob HMAC for transaction ({self.transaction_id}) verified successfully.",
        )

    @staticmethod
    def verify_signature(**kwargs):
        """
        Compute hmac and compare with recieved hmac for authenticity
        Raise WebhookServiceError if verification fails

        :param received_hmac: signature received from webhook
        :param concatenated_fields: combined string of relevant fields
         to compute HMAC
        :param secret_key: secret key used for HMAC computation
        :param digiestmod: hashing algorithm to use (default: sha512)
        """
        encode_key = kwargs["secret_key"].encode("utf-8")
        encode_fields = kwargs["concatenated_fields"].encode("utf-8")
        received_hmac = kwargs["received_hmac"]
        digiestmod = kwargs.get("digestmod", hashlib.sha512)
        calculate_hmac = hmac.new(
            encode_key, encode_fields, digestmod=digiestmod
        ).hexdigest()

        if not (hmac.compare_digest(calculate_hmac, received_hmac)):
            logger.error("Received HMAC doesn't match processed HMAC.")
            raise WebhookServiceError(
                "Verification hmac failed..",
                "HMAC_FAIL",
            )
