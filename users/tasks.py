from celery import shared_task,Task
from users.services.expired_code import remove_expired_code
import logging
log = logging.getLogger(__name__)

@shared_task(bind=True,queue='expired',max_retries=3)
def remove_expired_task(self:Task):
    '''
    Celery backgroud task for clean up any expired EmailCode object;
    '''
    try:
        log.info({'Event':'Start cleaning useless code'})
        remove_expired_code()
        log.info({'Event':'End with cleaning'})
    except Exception as exc:
        log.exception({'Error':'Expired code cleaner failed!'})
        raise self.retry(exc=exc, countdown=60)
    
