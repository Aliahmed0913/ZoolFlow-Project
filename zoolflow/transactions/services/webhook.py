import logging
import hashlib
import hmac
from django.conf import settings
from .helpers import bring_transaction

logger = logging.getLogger(__name__)


class WebhookServiceError(Exception):
    # Raised when Webhook handling fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class WebhookService:
    def __init__(self, data, merchant_id, transaction_id):
        self.data = data
        self.transaction = bring_transaction(merchant_order_id=merchant_id)
        self.transaction_id = transaction_id

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
