from django.utils import timezone
from enum import Enum
from datetime import timedelta
import logging, secrets

from users.models import EmailCode,User
from Restaurant.settings import CODE_LENGTH

logger = logging.getLogger(__name__)

class VerifyCodeStatus(Enum):
    VALID = 'valid'
    NOT_FOUND = 'not_found'
    EXPIRED = 'expired'
    IN_VALID = 'in_valid'
class VerificationCodeService:
    
    DEFAULT_EXPIRY = timedelta(minutes=10)
    
    def __init__(self,user_id):
        self.user = User.objects.get(id=user_id)

    def create_code(self, expiry:timedelta=None):
        ''' expiry time for code with default to 10 minute'''
        generated_email_code = EmailCode.objects.create(
            user=self.user,
            code=self.generate_code(),
            expiry_time=timezone.now() + (expiry or self.DEFAULT_EXPIRY)
        )
        
        logger.info(f'New code successfuly created for {self.user.username}.')
        return generated_email_code
    
    def validate_code(self,received_code:str):
        '''Check if there an active code for requested user and evaluate it with received_code'''
        actual_code = self.active_code()
        
        if not actual_code:
            logger.warning(f'there is no active code for {self.user.username}')            
            return VerifyCodeStatus.NOT_FOUND
    
        if self.is_expired_code(actual_code):
            return VerifyCodeStatus.EXPIRED
    
        elif str(actual_code.code) == received_code:
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])
            self.disable_code(actual_code)
            logger.info(f'welcome {self.user.username} your account has verified')
            return VerifyCodeStatus.VALID
        
        logger.warning('this invalid code') 
        return VerifyCodeStatus.IN_VALID
    
    def recreate_code_on_demand(self):
        current_code = self.active_code()
        
        if not current_code or self.is_expired_code(current_code):
                self.create_code() 
                return True
        
        remaining = current_code.expiry_time - timezone.now()
        logger.info(f'verify code has {remaining.seconds // 60} minute left')    
        return False
    
    def is_expired_code(self,code):
        if code.expiry_time <= timezone.now():
            logger.warning('code is expired!')
            self.disable_code(code)
            return True
        return False   
    
    def disable_code(self,code):
        ''' Marked code as Used'''
        code.is_used = True
        code.save(update_fields=['is_used'])

    
    def active_code(self):
        return EmailCode.objects.filter(user_id=self.user.id, is_used=False).order_by('-created_at').first()
    
    def generate_code(self):
        '''
        Generate numeric verification code.
        '''
        min_value = 10 ** (CODE_LENGTH - 1)
        max_value = (10 ** CODE_LENGTH) - 1 
        return secrets.randbelow(max_value - min_value + 1) + min_value
    
    