import logging
from datetime import date
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext as _
from django.conf import settings
from .services.normalizers import normalize_phone_number

logger = logging.getLogger(__name__)

CUSTOMER_NAME_LENGTH = getattr(settings, "CUSTOMER_NAME_LENGTH")
ALLOW_AGE = getattr(settings, "ALLOW_AGE")

EGYPT_POSTAL_REGX = RegexValidator(
    regex=r"^\d{5}$", message="In Egypt must be five digits."
)


def validate_phone_number(value: str):
    normalize_phone_number(value=value)


def validate_first_name(value: str):
    if not value[0].isupper():
        logger.warning("Customer name must start with uppercase letter")
        raise ValidationError(_("Name must start with an uppercase letter."))
    if len(value) < CUSTOMER_NAME_LENGTH:
        logger.warning(
            f"Customer name must be more than {CUSTOMER_NAME_LENGTH} characters."
        )
        raise ValidationError(
            _(f"Name must be more than {CUSTOMER_NAME_LENGTH} characters.")
        )


def valid_age(value: date):
    today = date.today()
    if value >= today:
        logger.warning("Invalid date of birth")
        raise ValidationError(_("Invalid date of birth"))

    # check if the month,day for today is before birthday month,day return true(1) else false(0)
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age >= ALLOW_AGE:
        return value
    logger.warning("The customer is underage.")
    raise ValidationError(_("Customer too young"))
