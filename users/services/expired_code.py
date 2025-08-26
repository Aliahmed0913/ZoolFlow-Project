from users.models import EmailCode
from django.utils.timezone import now
import logging
logger = logging.getLogger(__name__)

def remove_expired_code(limit=500):
    '''Remove expired EmailCode records from DB in batches
     
       Arg:
       limit (int): rate the limite of delete per batch
    '''
    while True:
        expired_codes = EmailCode.objects.filter(expiry_time__lt=now())[:limit]
        count = expired_codes.count()
        if not count:
            break
        expired_codes.delete()
        logger.info({'event':'expired_codes_cleanup', 'deleted_count':{count}})
    