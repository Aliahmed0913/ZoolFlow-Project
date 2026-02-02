import pytest
from users.models import User
from django.db.models.signals import post_save
from users.signals import initiate_verification_code


@pytest.fixture(scope="function")
def create_activate_user(db, mocker):
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
        post_save.connect(initiate_verification_code, sender=User)
        return user

    return make_user


@pytest.fixture()
def authenticate_client(api_client, create_activate_user, mocker):
    mocker.patch("users.signals.handle_user_registeration_verify_code")
    user = create_activate_user()
    api_client.force_authenticate(user=user)
    return user
