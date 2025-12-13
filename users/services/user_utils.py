from users.models import EmailCode
from django.utils.timezone import now
import logging
logger = logging.getLogger(__name__)

def remove_expired_code(limit=500):
    '''Remove expired EmailCode records from DB in batches
     
       Arg:
       limit (int): number of record to delete per batch
    '''
    logger.info({'event':'expired_codes_cleanupp start...'})
    while True:
        expired_code_ids = list(
            EmailCode.objects
            .filter(expiry_time__lt=now())
            .values_list('id',flat=True)[:limit]
            )
        
        if not expired_code_ids:
            break
        
        deleted_count, _ = EmailCode.objects.filter(id__in=expired_code_ids).delete() 
        logger.info({'event':'expired_codes_cleanup', 'deleted_count':deleted_count})
    logger.info({'event':'expired_codes_cleanup done'})
    
    
    
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

def get_token_from_cookie(request):
    '''
    Return RefreshToken object if there an refresh token in the request cookie
    ,error message if one exist
        
    :param request: POST request usually
    '''
    ref_token = request.COOKIES.get('refresh_token')
    if not ref_token:
        return None,'No refresh token in cookie'
    try:
        refresh = RefreshToken(ref_token)
        return refresh, None
    except TokenError:
        return None, 'invalid or expired refresh token'
    
    