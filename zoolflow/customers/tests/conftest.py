import pytest
from django.db.models.signals import post_save
from ..models import Customer
from ..services.helpers import initialize_customer
from zoolflow.users.signals import initiate_verification_code
from zoolflow.users.models import User


@pytest.fixture(scope="function")
def create_activate_user(db):
    post_save.disconnect(initiate_verification_code, sender=User)

    def make_user(**kwargs):
        user = User.objects.create_user(
            username=kwargs.get("username", "Aliahmed"),
            password=kwargs.get("password", "Aliahmed091$"),
            role_management=kwargs.get("role_management", User.Roles.CUSTOMER),
            email=kwargs.get("email", "example998@cloud.com"),
            is_active=kwargs.get("is_active", False),
        )
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user

    yield make_user
    post_save.connect(initiate_verification_code, sender=User)


@pytest.fixture()
def _create_customer(create_activate_user):
    def start_customer(**kwargs):
        user = create_activate_user(**kwargs)
        initialize_customer(id=user.id)
        return user, Customer.objects.get(user=user)

    return start_customer
