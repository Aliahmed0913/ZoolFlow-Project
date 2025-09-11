import phonenumbers 
from phonenumbers.phonenumberutil import NumberParseException
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_phone(value):
    try:
        phonenumber = phonenumbers.parse(value)
    
        if not phonenumbers.is_possible_number(phonenumber):
            raise ValidationError(_('Format is not possible'))
    
        if not phonenumbers.is_valid_number(phonenumber):
            raise ValidationError(_('Not valid for specific region'))
    
    except NumberParseException:
        raise ValidationError(_('Missing or invalid international format.'))
    
    return str(phonenumbers.format_number(phonenumber,phonenumbers.PhoneNumberFormat.E164))