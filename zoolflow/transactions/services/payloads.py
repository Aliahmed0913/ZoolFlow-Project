from django.conf import settings
from zoolflow.customers.services.helpers import currency_and_address


def order_payload(amount_cents, token, merchant_id, customer):
    """
    Set payload for creating an order in provider
    """

    currency, _ = currency_and_address(customer)
    payload = {
        "auth_token": token,
        "delivery_needed": "false",
        "merchant_order_id": merchant_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "items": [],
    }
    return payload


def payment_token_payload(amount_cents, token, order_id, customer):
    """
    Set payload for requesting the payment key token
    """

    currency, address = currency_and_address(customer=customer)
    payload = {
        "auth_token": token,
        "amount_cents": amount_cents,
        "currency": currency,
        "order_id": order_id,
        "billing_data": {
            "apartment": address.apartment_number or "NA",
            "email": customer.user.email or "Na",
            "first_name": customer.first_name or "NA",
            "last_name": customer.last_name or "un-known",
            "street": address.line or "NA",
            "building": address.building_number or "NA",
            "phone_number": customer.phone_number or "NA",
            "postal_code": address.postal_code or "NA",
            "city": address.city or "NA",
            "country": address.country.name or "NA",
            "state": address.state or "NA",
            "floor": "NA",
            "shipping_method": "PKG",
        },
        "integration_id": getattr(settings, "PAYMOB_PAYMENT_KEY"),
    }

    return payload
