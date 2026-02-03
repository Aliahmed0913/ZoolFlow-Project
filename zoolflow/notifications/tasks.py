import logging
from celery import shared_task
from .mailers.senders import mail_transaction_state, mail_verify_code
from zoolflow.users.models import VerificationCode

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def verification_code_mail_task(self, emailcode_id):
    """Backgroud task for mailing verify code to user email"""
    try:
        logger.info("start mail your code...")
        emailcode = VerificationCode.objects.get(id=emailcode_id)
        mail_verify_code(emailcode)
        logger.info("your code mailed successfully.")
    except Exception as e:
        logger.warning("fail to send you code verification retry in minute...")
        self.retry(exc=e, countdown=60)
        raise


@shared_task
def transaction_state_email_task(transaction_id):
    """
    Background task for mailing transaction state to user email
    """
    logger.info(f"Start mailing transaction {transaction_id} state...")
    # Assuming mail_transaction_state is a function that sends the email
    mail_transaction_state(transaction_id)