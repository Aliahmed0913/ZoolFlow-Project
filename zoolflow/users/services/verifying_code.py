import logging
import secrets
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from ..models import User
from zoolflow.notifications.tasks import verification_code_mail_task

logger = logging.getLogger(__name__)


class VerificationCodeServiceError(Exception):
    pass


class VerificationCodeService:
    def __init__(self, email):
        self.code_lifetime = getattr(settings, "CODE_LIFETIME", 60 * 2)
        self.email = email

    def create_verification_code(self):
        """
        Create an verification code and forward it to user email
        """
        # check if the user has been verified before
        user = User.objects.filter(Q(email__exact=self.email) & Q(is_active=False))
        # check if there is no active code for that user
        verify_code = cache.get(self.email)
        if user and not verify_code:
            code_length = getattr(settings, "CODE_LENGTH")
            # if 3 digit code the lower boud 100
            min_value = 10 ** (code_length - 1)
            # upper bound for 6 digit 999
            max_value = (10**code_length) - 1
            # maximum variety range with secrets =>(0 to 900)+ 100
            code = secrets.randbelow(max_value - min_value + 1) + min_value

            cache.set(self.email, code, timeout=self.code_lifetime)

            logger.info(f"Verification Code successfully created for {self.email}.")

            # call celery task to start mailing verification-code
            verification_code_mail_task.delay(self.email)

        elif verify_code:
            logger.error("Try again")
            raise VerificationCodeServiceError(
                "Current verification code is valid, Try again"
            )
        else:
            raise VerificationCodeServiceError(
                f"{self.email} account is already active, login please"
            )

    def validate_code(self, received_code: str):
        """
        Check if there an active code for requested user,
        and evaluate it with received_code.
        """
        verify_code = str(cache.get(self.email))
        # check user input code with the one we forward to him
        if verify_code == received_code:
            with transaction.atomic():
                user = (
                    User.objects.select_for_update()
                    .filter(email__iexact=self.email)
                    .first()
                )
                # activate the user
                user.is_active = True
                user.save(update_fields=["is_active"])
                logger.info(f"Account {self.email} activated.")
            cache.delete(self.email)
        else:
            logger.error(f"{self.email} entered code is invalid")
            raise VerificationCodeServiceError("verify code invalid.")
