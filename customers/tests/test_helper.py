import pytest
from ..services.helpers import country_and_currency, SupportedCountryError


@pytest.mark.django_db()
class TestCountryAndCurrencyHelper:
    def test_correct_currency(self, customer_factory):
        customer = customer_factory(
            username="Currency_return", email="Currency-return009@gmail.com"
        )
        currency, _ = country_and_currency(customer.id, customer.user.username)
        assert currency == "EGP"

    @pytest.mark.parametrize(
        "have_address,country",
        [(False, None), (True, "SD")],  # no main address raise error here
    )  # unsupported country raise error here
    def test_fail_currency(
        self, customer_factory, paymob_factory, have_address, country
    ):
        customer = customer_factory(with_address=have_address, country=country)

        with pytest.raises(SupportedCountryError):
            country_and_currency(customer.id, customer.user.username)
