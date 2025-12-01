import pytest
from rest_framework.test import APIClient
from django.db.models.signals import post_save
from users.models import User
from users.signals import handle_user_registeration_verify_code

@pytest.fixture(scope='session')
def api_client():
    return APIClient()

@pytest.fixture
def mock_mail(mocker):
    return mocker.patch('notifications.services.verification_code.mail_code_task.delay')



@pytest.fixture(scope='function')
def create_activate_user(db,mocker):
    post_save.disconnect(handle_user_registeration_verify_code,sender=User)
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
        post_save.connect(handle_user_registeration_verify_code,sender=User)
        return user
    return make_user