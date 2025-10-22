import pytest
from users.models import EmailCode
from django.utils import timezone
from users.services.expired_code import remove_expired_code
from users.services.verifying_code import VerificationCodeSerivce as vcs,CodeNotFoundError,CodeExpiredError,InvalidCodeError

@pytest.mark.django_db
class TestVerificationCodeService:
    def test_create_code(self,create_user):
        user1 = create_user() # un active user
        verify_code = vcs(user_email=user1.email)
        created_code = verify_code.create_code(expiry=None) # can specify the live of our code (expiry) timedelta
        code_instance = EmailCode.objects.get(user_id=user1.id)        
        assert code_instance is not None
        assert int(code_instance.code) == created_code.code 
    
    def test_validate_code_not_found(self,create_user):
        received_code = '123456'
        user1 = create_user()
        # Not found code case 
        verify_code = vcs(user_email=user1.email)
        with pytest.raises(CodeNotFoundError):
            verify_code.validate_code(received_code=received_code)     
        assert not user1.is_active
    
    def test_validate_code_expired(self,create_user,email_code):    
        user1 = create_user()
        # Expired code case 
        verify_code = vcs(user_email=user1.email)
        expired_code = email_code(user=user1,expiry_time=timezone.now()) # expired code
        
        with pytest.raises(CodeExpiredError):
            verify_code.validate_code(received_code='123456')
        expired_code.refresh_from_db()
        assert expired_code.is_used 
    
    def test_validate_code_invalid(self,create_user,email_code):    
        user1 = create_user()
        # Invalid code case 
        verify_code = vcs(user_email=user1.email)
        email_code(user=user1) # valid code
        
        with pytest.raises(InvalidCodeError):
            verify_code.validate_code(received_code='')
        assert not user1.is_active
    
    def test_validate_code_valid(self,create_user,email_code):    
        user1 = create_user()
        # Valid code case
        email_code(user=user1) # valid code
        verify_code = vcs(user_email=user1.email)
        result,user1 = verify_code.validate_code(received_code='123456')
        user1.refresh_from_db()
        code = EmailCode.objects.get(user=user1)
        assert result == verify_code.VerifyCodeStatus.VALID
        assert user1.is_active
        assert code.is_used
    
    @pytest.mark.parametrize('user,verify_code_status,next_status',[('customer',vcs.VerifyCodeStatus.ACTIVE,None),('p_customer',vcs.VerifyCodeStatus.CREATED,vcs.VerifyCodeStatus.VALID)])
    def test_recreate_code(self,simple_users,email_code,verify_code_status,user,next_status):
        ''' Test recreate_code_on_demand behavior for active and inactive users'''
        # Active user case
        user1 = simple_users[user]
        verify_code = vcs(user_email=user1.email)
        if user1.is_active:
            result = verify_code.recreate_code_on_demand()
            assert result == verify_code.VerifyCodeStatus.ACTIVE
        else:
            # Expired code or user doesn't received a verify code case
            # create a new code
            email_code(user=user1,expiry_time=timezone.now())
            result = verify_code.recreate_code_on_demand()
            valid_code = EmailCode.objects.filter(user=user1,is_used=False)

            assert result == verify_code_status 
            assert valid_code is not None

            # Attemp to recreate a code when a valid code exist
            result = verify_code.recreate_code_on_demand()
            assert result == next_status
        
        
@pytest.mark.django_db
def test_rm_expired_code(simple_users,email_code):
    user1= simple_users['staff']
    user2= simple_users['customer']
    expired_code=email_code(user=user1,expiry_time=timezone.now())
    valide_code=email_code(user=user2)
    
    # work in real-execution with celery beat
    remove_expired_code()
        
    assert not EmailCode.objects.filter(id=expired_code.id).exists(),'expired code has been deleted'
    assert EmailCode.objects.filter(id=valide_code.id).exists() , 'valide code remain'
    assert EmailCode.objects.count() == 1

     
