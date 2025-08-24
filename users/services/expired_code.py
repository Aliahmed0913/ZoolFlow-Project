from users.models import EmailCode
from django.utils.timezone import now
import logging
logger = logging.getLogger(__name__)
def remove_expired_code():
    expired_codes = EmailCode.objects.filter(expiry_time__lt=now())
    count = expired_codes.count()
    expired_codes.delete()
    logger.info({'message':f'{count} code has deleted'})
    