import logging
from celery import shared_task
from .mailers.senders import mail_transaction_state, mail_verify_code

logger = logging.getLogger(__name__)


@shared_task
def verification_code_mail_task(user_email):
    """Backgroud task for mailing verify code to user email"""

    logger.info("start mailing verification code...")
    mail_verify_code(user_email)


@shared_task
def transaction_state_email_task(transaction_id):
    """
    Background task for mailing transaction state to user email
    """
    logger.info(f"Start mailing transaction {transaction_id} state...")
    # Assuming mail_transaction_state is a function that sends the email
    mail_transaction_state(transaction_id)
