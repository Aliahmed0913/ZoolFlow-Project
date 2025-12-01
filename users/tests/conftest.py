import pytest
from django.conf import settings
from rest_framework.test import APIClient
from users.models import User,EmailCode
from django.db.models.signals import post_save
from notifications.signals import handle_verify_code_mail as notif_signals
from customers.signals import handle_activation_user as user_signal


@pytest.fixture(scope="session", autouse=True)
def fast_password_hasher():
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

@pytest.fixture()
def simple_users(db):
    admin = User.objects.create_user(username='admin',password='Aliahmed091$',email = 'admin998@example.com',role_management = User.Roles.ADMIN)
    staff = User.objects.create_user(username='staff',password='Aliahmed091$',email = 'staff998@example.com',role_management = User.Roles.STAFF)
    customer = User.objects.create_user(username='customer',password='Aliahmed091$',email = 'customer998@example.com',role_management = User.Roles.CUSTOMER)
    passive_customer = User.objects.create_user(username='p_customer',password='Aliahmed091$',email = 'P_customer998@example.com',role_management = User.Roles.CUSTOMER,is_active=False)

    return {'admin':admin, 'staff':staff, 'customer':customer, 'p_customer':passive_customer}

@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return User.objects.create_user(
            username = kwargs.get('username','Aliahmed'),
            password = kwargs.get('password','Aliahmed091$'),
            role_management = kwargs.get('role_management',User.Roles.CUSTOMER),
            email = kwargs.get('email','example998@cloud.com'),
            is_active=kwargs.get('is_active',False)
          )
    return make_user

from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def email_code(db):
    def create_email_code(**kwargs):
        return EmailCode.objects.create(
            user = kwargs.get('user'),
            code = kwargs.get('code','123456'),
            expiry_time = kwargs.get('expiry_time',timezone.now()+timedelta(minutes=10)),
            is_used = kwargs.get('is_used',False),
        )
    return create_email_code
