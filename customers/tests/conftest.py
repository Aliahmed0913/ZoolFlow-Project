import pytest
from users.models import User
from rest_framework.test import APIClient

@pytest.fixture(scope='session')
def api_client():
    return APIClient()

@pytest.fixture
def create_activate_user(db):
    def make_user(**kwargs):
        user = User.objects.create_user(
            username = kwargs.get('username','Aliahmed'),
            password = kwargs.get('password','Aliahmed091$'),
            role_management = kwargs.get('role_management',User.Roles.CUSTOMER),
            email = kwargs.get('email','example998@cloud.com'),
            is_active=kwargs.get('is_active',False)
          )
        user.is_active = True
        user.save(update_fields=['is_active'])
        return user
    return make_user

@pytest.fixture
def mock_mail(mocker):
    return mocker.patch('notifications.services.verification_code.mail_code_task.delay')