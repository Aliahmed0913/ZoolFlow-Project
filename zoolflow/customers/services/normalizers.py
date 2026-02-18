import logging
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def normalize_phone_number(value: str, default_region: str = "EG"):
    try:
        phonenumber = phonenumbers.parse(value, default_region)

        if not phonenumbers.is_possible_number(phonenumber):
            logger.warning("phone_number format is not possible.")
            raise ValidationError(_("Format is not possible"))

        if not phonenumbers.is_valid_number(phonenumber):
            logger.warning("phone_number not valid for specific region.")
            raise ValidationError(_("Not valid for specific region"))

    except NumberParseException:
        logger.warning("phone_number is missing or invalid international format.")
        raise ValidationError(_("Missing or invalid international format."))

    return str(
        phonenumbers.format_number(phonenumber, phonenumbers.PhoneNumberFormat.E164)
    )
