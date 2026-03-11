from django.db import transaction
import pytest
from django.core.cache import cache
from ..services.verifying_code import (
    VerificationCodeService,
    VerificationCodeServiceError,
)


@pytest.mark.django_db
class TestVerificationCodeService:
    def test_create_code_sets_cache_and_triggers_mail(self, create_user, mock_mail):
        user = create_user(is_active=False)
        cache.delete(user.email)
        service = VerificationCodeService(email=user.email)

        service.create_verification_code()

        cached_code = cache.get(user.email)
        assert cached_code is not None
        assert mock_mail.called

    def test_create_code_rejects_if_code_already_exists(
        self, create_user, verification_code_cache
    ):
        user = create_user(is_active=False)
        cache.delete(user.email)
        verification_code_cache(user.email, code="123456")
        service = VerificationCodeService(email=user.email)

        with pytest.raises(VerificationCodeServiceError):
            service.create_verification_code()

    def test_create_code_rejects_if_user_is_already_active(self, create_user):
        user = create_user(is_active=True)
        service = VerificationCodeService(email=user.email)

        with pytest.raises(VerificationCodeServiceError):
            service.create_verification_code()

    def test_validate_code_activates_user_and_deletes_cache(
        self, create_user, verification_code_cache, mocker
    ):
        user = create_user(is_active=False)
        verification_code_cache(user.email, code="654321")
        mock_init_customer = mocker.patch(
            "zoolflow.users.services.verifying_code.initialize_customer"
        )
        mocker.patch.object(transaction, "on_commit", lambda fn: fn())
        service = VerificationCodeService(email=user.email)

        service.validate_code(received_code="654321")

        user.refresh_from_db()
        assert user.is_active is True
        assert cache.get(user.email) is None
        assert mock_init_customer.called

    def test_validate_code_rejects_invalid_code(
        self, create_user, verification_code_cache
    ):
        user = create_user(is_active=False)
        verification_code_cache(user.email, code="111111")
        service = VerificationCodeService(email=user.email)

        with pytest.raises(VerificationCodeServiceError):
            service.validate_code(received_code="999999")

        user.refresh_from_db()
        assert user.is_active is False
