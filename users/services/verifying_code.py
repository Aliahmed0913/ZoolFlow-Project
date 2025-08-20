from users.models import User,EmailCode
from django.utils import timezone
from datetime import timedelta
from users.task import mail_user_code
import random, logging

logger = logging.getLogger(__name__)
EXPIRY_CODE = timedelta(minutes=10)

def re_create_verify_code(user):
    current_code = EmailCode.objects.filter(user_id=user.id, is_used=False).order_by('-created_at').first()
    
    if current_code:
       
        if timezone.now() >= current_code.expiry_time:
            current_code.is_used = True
            current_code.save(update_fields=['is_used'])
            return create_email_code(user=user) 
        
        remaining = current_code.expiry_time - timezone.now()
        logger.info(f'verify code has {remaining.seconds // 60} minute left')    
        mail_user_code.delay(current_code.id)
        return current_code
           
    return create_email_code(user=user)
    
            
def create_email_code(user:User):
    generated_email_code = EmailCode.objects.create(
        user=user,
        code=generate_code(),
        expiry_time=timezone.now() + EXPIRY_CODE
    )
    logger.info(f'New code successfuly created for {user.username}.')
    mail_user_code.delay(generated_email_code.id)
    return generated_email_code
    
def generate_code():
    return random.randint(100000,999999)