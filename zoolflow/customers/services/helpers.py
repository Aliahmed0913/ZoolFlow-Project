import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from ..models import Customer, Address, KnowYourCustomer

logger = logging.getLogger(__name__)

User = get_user_model()


@transaction.atomic
def initialize_customer(id):
    user = User.objects.get(id=id)
    customer = Customer.objects.create(user=user)
    Address.objects.create(customer=customer, main_address=True)
    KnowYourCustomer.objects.create(customer=customer)
    return customer


class SupportedCountryError(Exception):
    """Raised when the customer's country is unsupported"""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


def currency_and_address(customer):
    """
    Return the customer's local currency,country
    based on their current main address
    """
    # Get customer main address
    address = Address.objects.filter(
        customer_id=customer.id,
        main_address=True,
    )
    if not address:
        logger.error(
            f"There is no main address specified for {customer.user.username}."
        )
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
        f"Customer {customer.user.username} local currency has been successfully determined",
    )

    return currency, address
