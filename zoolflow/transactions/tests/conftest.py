import pytest
from django.contrib.auth import get_user_model
from ..services.paymob import PayMobClient
from customers.models import Customer, Address

User = get_user_model()


@pytest.fixture()
def customer_factory(db):
    def create_customer(with_address=True, **kwargs):
        user = User.objects.create_user(
            username=kwargs.get("username", "Aliahmed"),
            password=kwargs.get("password", "Aliahmed091$"),
            role_management=kwargs.get("role_management", User.Roles.CUSTOMER),
            email=kwargs.get("email", "example998@cloud.com"),
        )
        customer = Customer.objects.create(user=user)

        if with_address:
            Address.objects.create(
                customer=customer,
                main_address=kwargs.get("main_address", True),
                country=kwargs.get("country", "EG"),
            )

        return customer

    return create_customer


@pytest.fixture()
def paymob_factory():
    def create_paymob(customer):
        return PayMobClient(
            customer=customer,
            currency="EGP",
            address="test address",
            merchant_id="test-merchant-id",
        )

    return create_paymob


@pytest.fixture
def mock_post(mocker):
    session = mocker.Mock()
    mock_response = mocker.Mock()
    session.post.return_value = mock_response
    mocker.patch(
        "transactions.services.paymob.get_session_with_retries", return_value=session
    )
    return mock_response
