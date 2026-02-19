import pytest
from django.core.cache import cache
from ..models import Address, Customer, KnowYourCustomer
from zoolflow.users.models import User
from zoolflow.users.services.verifying_code import VerificationCodeService


@pytest.mark.django_db()
class TestSignals:
    def test_kyc_approved_sets_customer_verified(self, _create_customer):
        _, customer = _create_customer(
            username="sig_approved",
            email="sig_approved@example.com",
        )
        kyc = KnowYourCustomer.objects.get(customer=customer)
        kyc.status_tracking = KnowYourCustomer.Status.APPROVED
        kyc.save(update_fields=["status_tracking"])
        customer.refresh_from_db()
        assert customer.is_verified is True

    def test_kyc_rejected_sets_customer_not_verified(self, _create_customer):
        _, customer = _create_customer(
            username="sig_rejected",
            email="sig_rejected@example.com",
        )
        kyc = KnowYourCustomer.objects.get(customer=customer)
        customer.is_verified = True
        customer.save(update_fields=["is_verified"])
        kyc.status_tracking = KnowYourCustomer.Status.REJECTED
        kyc.save(update_fields=["status_tracking"])
        customer.refresh_from_db()
        assert customer.is_verified is False

    def test_kyc_pending_keeps_customer_not_verified(self, _create_customer):
        _, customer = _create_customer(
            username="sig_pending",
            email="sig_pending@example.com",
        )
        kyc = KnowYourCustomer.objects.get(customer=customer)
        kyc.status_tracking = KnowYourCustomer.Status.PENDING
        kyc.save(update_fields=["status_tracking"])
        customer.refresh_from_db()
        assert customer.is_verified is False


@pytest.mark.django_db(transaction=True)
def test_customer_entities_are_created_after_email_verification(mocker):
    mocker.patch("zoolflow.users.services.verifying_code.verification_code_mail_task.delay")
    user = User.objects.create_user(
        username="verify_flow",
        email="verify_flow@example.com",
        password="Aliahmed091$",
        role_management=User.Roles.CUSTOMER,
        is_active=False,
    )
    assert Customer.objects.filter(user=user).exists() is False

    cache.set(user.email, "123456", timeout=120)
    VerificationCodeService(email=user.email).validate_code(received_code="123456")

    user.refresh_from_db()
    assert user.is_active is True

    customer = Customer.objects.get(user=user)
    assert Address.objects.filter(customer=customer, main_address=True).count() == 1
    assert KnowYourCustomer.objects.filter(customer=customer).count() == 1
