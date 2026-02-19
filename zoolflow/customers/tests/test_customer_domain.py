from datetime import date
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Address, Customer, KnowYourCustomer
from ..services.helpers import (
    SupportedCountryError,
    currency_and_address,
    initialize_customer,
)
from ..services.normalizers import normalize_phone_number
from ..validators import validate_first_name, validate_phone_number, valid_age


@pytest.mark.django_db()
class TestModelsAndHelpers:
    def test_customer_str_uses_first_name_or_username(self, _create_customer):
        user, customer = _create_customer(
            username="str_user", email="str_user@example.com"
        )
        customer.first_name = "Ali"
        customer.save(update_fields=["first_name"])
        assert str(customer) == "Ali"

        customer.first_name = ""
        customer.save(update_fields=["first_name"])
        assert str(customer) == user.username

    def test_kyc_str_contains_customer_and_document_type(self, _create_customer):
        _, customer = _create_customer(username="kyc_str", email="kyc_str@example.com")
        assert "national_id" in str(KnowYourCustomer.objects.get(customer=customer))

    def test_set_main_address_switches_main_flag(self, _create_customer):
        _, customer = _create_customer(
            username="addr_switch",
            email="addr_switch@example.com",
        )
        first = Address.objects.get(customer=customer, main_address=True)
        second = Address.objects.create(
            customer=customer,
            state="Cairo",
            city="Cairo",
            line="Street",
            building_number="10",
            apartment_number="2",
            postal_code="12345",
            main_address=False,
        )
        second.set_main_address()
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.main_address is False
        assert second.main_address is True

    def test_unique_constraint_prevents_two_main_addresses(self, _create_customer):
        _, customer = _create_customer(
            username="unique_main",
            email="unique_main@example.com",
        )
        with pytest.raises(IntegrityError):
            Address.objects.create(
                customer=customer,
                state="Giza",
                city="Giza",
                line="Street",
                building_number="8",
                apartment_number="1",
                postal_code="12345",
                main_address=True,
            )

    def test_initialize_customer_creates_customer_address_and_kyc(
        self, create_activate_user
    ):
        user = create_activate_user(
            username="init_customer",
            email="init_customer@example.com",
        )
        customer = initialize_customer(id=user.id)
        assert Customer.objects.filter(pk=customer.pk, user=user).exists()
        assert Address.objects.filter(customer=customer, main_address=True).count() == 1
        assert KnowYourCustomer.objects.filter(customer=customer).count() == 1

    def test_currency_and_address_returns_currency_for_supported_country(
        self, _create_customer
    ):
        _, customer = _create_customer(
            username="supported_currency",
            email="supported_currency@example.com",
        )
        currency, address = currency_and_address(customer)
        assert currency == "EGP"
        assert address.customer_id == customer.id

    def test_currency_and_address_raises_without_main_address(self, _create_customer):
        _, customer = _create_customer(username="no_main", email="no_main@example.com")
        Address.objects.filter(customer=customer).update(main_address=False)
        with pytest.raises(SupportedCountryError):
            currency_and_address(customer)

    def test_currency_and_address_raises_for_unsupported_country(
        self, _create_customer
    ):
        _, customer = _create_customer(
            username="unsupported_currency",
            email="unsupported_currency@example.com",
        )
        address = Address.objects.get(customer=customer, main_address=True)
        address.country = "SD"
        address.save(update_fields=["country"])
        with pytest.raises(SupportedCountryError):
            currency_and_address(customer)


class TestValidatorsAndNormalizers:
    def test_validate_first_name_rejects_lowercase(self):
        with pytest.raises(ValidationError):
            validate_first_name("ali")

    def test_validate_first_name_rejects_short_name(self):
        with pytest.raises(ValidationError):
            validate_first_name("Al")

    def test_validate_first_name_allows_blank(self):
        validate_first_name("")

    def test_validate_phone_number_rejects_invalid(self):
        with pytest.raises(ValidationError):
            validate_phone_number("invalid")

    def test_normalize_phone_number_returns_e164(self):
        assert normalize_phone_number("01012345678") == "+201012345678"

    def test_valid_age_rejects_future_date(self):
        with pytest.raises(ValidationError):
            valid_age(date.today())

    def test_valid_age_rejects_underage(self):
        underage = date.today().replace(year=date.today().year - 10)
        with pytest.raises(ValidationError):
            valid_age(underage)
