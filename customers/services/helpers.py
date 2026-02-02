import logging
from django.conf import settings
from ..models import Address

logger = logging.getLogger(__name__)


class SupportedCountryError(Exception):
    """Raised when the customer's country is unsupported"""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


def country_and_currency(customer_id, username):
    """
    Return the customer's local currency,country
    based on their main_address
    """
    # Get customer main address
    address = Address.objects.filter(
        customer_id=customer_id,
        main_address=True,
    )
    if not address:
        logger.error(f"There is no main address specified for {username}.")
        raise SupportedCountryError(
            message="There is no main address specified", details="Address"
        )
    address = address.first()
    # Get currency for that country based on our supported countries
    currency = getattr(settings, "SUPPORTED_COUNTRIES", {}).get(address.country.name)
    if not currency:
        logger.error("Currency for that country is unsupported.")
        raise SupportedCountryError(
            f"Country {address.country.name} not supported",
            details="Currency",
        )
    logger.info(
        f"Customer {username} local currency has been successfully determined",
    )

    return currency, address
