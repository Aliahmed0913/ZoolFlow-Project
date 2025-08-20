from celery import shared_task
from users.models import EmailCode
from notifications.services.send_code import mail_verify_code
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def mail_user_code(self,emailcode_id):
    try:
        logger.info('start mail you code...')
        emailcode = EmailCode.objects.get(id=emailcode_id)
        mail_verify_code(emailcode)
        logger.info('you recived code in you email')
    except Exception as e:
        logger.warning('fail to send you code verification retry in minute...')
        raise self.retry(exc=e, countdown=60)
   
   
   

# clean up expired code after hour