import logging
import requests
import json
import time
from django.core.cache import cache
from django.conf import settings
from redis.exceptions import LockError
from .http_client import get_session_with_retries
from .payloads import order_payload, payment_token_payload

logger = logging.getLogger(__name__)


class ProviderServiceError(Exception):
    # Raised when provider API fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class PayMobClient:
    def __init__(self, *args, **kwargs):
        self.customer = kwargs.get("customer", None)
        self.amount_cents = kwargs.get("amount_cents", None)
        self.session = get_session_with_retries()

    def _request_field(self, payload, endpoint, requested_field, field_name):
        """
        It's a POST request pattern.

        Return the requested field from the endpoint provided
        """
        try:
            response = self.session.post(
                url=endpoint,
                json=payload,
                timeout=getattr(settings, "CONNECTION_TIMEOUT", (5, 5)),
            )
            response.raise_for_status()

            data = response.json()
            result = data.get(requested_field)

            if not result:
                logger.error(f"No {field_name} returned from provider.")
                raise ProviderServiceError(
                    f"The API did not return the {field_name}.",
                    f"{field_name.capitalize()}",
                )

            logger.info(f"{field_name} has been successfully returned.")
            return result

        except requests.RequestException as pe:
            logger.error(f"Provider failed with error: {str(pe)}")
            raise ProviderServiceError("provider API fail", details=str(pe))

    def _get_auth_token(self):
        """
        Return the PayMob authentication token.
        By passing there API key
        """
        # loop to handle worker's who didn't acquire lock
        for _ in range(3):
            cache_key = getattr(settings, "PAYMOB_AUTH_CACH_KEY")
            # check for existing token in cache
            token = cache.get(cache_key)
            if token:
                logger.info("provider authentication token returned.")
                return token
            try:
                # lock to prevent race-condition with workers
                with cache.lock(f"{cache_key}:lock", timeout=15, blocking_timeout=2):
                    # check if there a worker fetch the token yet
                    token = cache.get(cache_key)
                    if token:
                        logger.info("provider authentication token returned.")
                        return token
                    # request for the token
                    payload = {"api_key": getattr(settings, "PAYMOB_API_KEY")}
                    token = self._request_field(
                        payload=payload,
                        endpoint=getattr(settings, "AUTH_PAYMOB_TOKEN"),
                        requested_field="token",
                        field_name="authentication token",
                    )

                    timeout = getattr(settings, "CACHE_LIFETIME")
                    cache.set(cache_key, token, timeout=timeout)
                    return token

            except LockError:
                time.sleep(0.5)

    def create_order(self, merchant_id):
        """
        Return order ID from provider.

        Raises:
            ProviderServiceError if the API fails or returns no order ID.
        """
        try:
            token = self._get_auth_token()
            payload = order_payload(
                self.amount_cents,
                token,
                merchant_id,
                self.customer,
            )
        except Exception as e:
            logger.error("failed on configure order payload")
            raise ProviderServiceError("Failed to handle order payload", str(e))

        order_id = self._request_field(
            payload=payload,
            endpoint=getattr(settings, "ORDER_PAYMOB_URL"),
            requested_field="id",
            field_name="order ID",
        )
        return order_id

    def payment_key_token(self, order_id):
        """
        Return the payment token specialized to who pay. Used to return an iframe
        """
        try:
            token = self._get_auth_token()
            payload = payment_token_payload(
                self.amount_cents,
                token,
                order_id,
                self.customer,
            )
        except Exception as e:
            logger.error("failed on configure payment token payload")
            raise ProviderServiceError("Failed to handle payment token payload", str(e))

        payment_token = self._request_field(
            payload=payload,
            endpoint=getattr(settings, "PAYMOB_PAYMENT_URL_KEY"),
            requested_field="token",
            field_name="payment token",
        )

        return payment_token

    def get_transaction_flags(self, transaction_id):
        """
        Return transaction status(flags) from paymob.

        By calling 'By Transacion ID' endpoint that take transaction id and Auth token
        """
        token = self._get_auth_token()
        header = {
            "Authorization": f"Bearer {token}",
        }
        url = f"https://accept.paymob.com/api/acceptance/transactions/{transaction_id}"
        try:
            response = self.session.get(url=url, headers=header)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Provider fail to return transaction current state")
            raise ProviderServiceError(
                "Provider fail to return transaction current state", str(e)
            )
        data = json.loads(response.content)
        return data
