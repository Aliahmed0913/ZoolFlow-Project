import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from datetime import date
from stackpay.settings import ALLOW_AGE,CUSTOMER_NAME_LENGTH 

def validate_customer_name(value:str):
    if not value[0].isupper():
        raise ValidationError(_('Name must start with an uppercase letter.'))
    if len(value) < CUSTOMER_NAME_LENGTH:
        raise ValidationError(_(F'Name must be more than {CUSTOMER_NAME_LENGTH} characters.'))
        
        
def validate_phone(value:str):
    try:
        phonenumber = phonenumbers.parse(value)
    
        if not phonenumbers.is_possible_number(phonenumber):
            raise ValidationError(_('Format is not possible'))
    
        if not phonenumbers.is_valid_number(phonenumber):
            raise ValidationError(_('Not valid for specific region'))
    
    except NumberParseException:
        raise ValidationError(_('Missing or invalid international format.'))
    
    return str(phonenumbers.format_number(phonenumber,phonenumbers.PhoneNumberFormat.E164))


def valid_age(value:date):
    today = date.today()
    if value >= today:
        raise ValidationError(_('Invalid date of birth'))
   
    # check if the month,day for today is before birthday month,day return true(1) else false(0)
    age = today.year - value.year - ((today.month,today.day) < (value.month,value.day))
    if age >= ALLOW_AGE:          
        return value
    raise ValidationError(_('Customer too young'))

    
    