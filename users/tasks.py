from celery import shared_task
from users.services.expired_code import remove_expired_code
import logging
log = logging.getLogger(__name__)


@shared_task(queue='expired',max_retries=3)
def remove_expired_task():
    log.info('start cleaning useless codes')
    remove_expired_code()
    log.info('end with cleaning')