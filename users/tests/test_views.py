import pytest
from users.models import EmailCode
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db(transaction=True)
def test_user_registration(api_call,mock_mail):
    # mock the verify code mail to not send the email realy 
    url = reverse('users:registration')
    
    payload = {
        'username':'GoodFather',
        'password':'Strong0913$',
        'email':'example0913@example.com',
    }
    response = api_call.post(path=url,data=payload,format='json')
    verify_code = EmailCode.objects.filter(user_id=response.data['id']).first()
    
    assert response.status_code == status.HTTP_201_CREATED
    assert verify_code is not None
    assert mock_mail.called
    
    # User with the same email tries to register, they are unacceptable
    response = api_call.post(path=url,data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
@pytest.mark.django_db()
class TestUserProfileViewSet:
    @pytest.mark.parametrize('role, excpected_status',[('customer',status.HTTP_403_FORBIDDEN),('staff',status.HTTP_200_OK)])
    def test_get_profiles(self,api_call,simple_users,role,excpected_status,mocker):
        # reset the login state
        api_call.force_authenticate(user=None)
        
        # Must be admin or staff for this action (see all users profiles)
        user1 = simple_users[role]
        url = reverse('users:user-profile-list')
        api_call.force_authenticate(user=user1)
        response = api_call.get(url)
        
        assert response.status_code == excpected_status
        
    def test_retrieve_update_profile(self,api_call,simple_users):
        # reset the login state
        api_call.force_authenticate(user=None)
        
        # Must be either admin or staff 
        user1 = simple_users['admin']
        user2 = simple_users['customer']
        
        api_call.force_authenticate(user=user1)
        url = reverse('users:user-profile-detail',kwargs={'pk':user1.id})
        response = api_call.get(url)
        
        assert response.data['id'] == user1.id 
        
        # Must be admin user for partial update the users profile 
        url = reverse('users:user-profile-detail',kwargs={'pk':user2.id})
        payload = {'username':'updated_name'}
        response = api_call.patch(url,data=payload)
        
        user2.refresh_from_db()
        assert user2.username == 'updated_name' == response.data['username']
        
            
    def test_update_get_own_profile(self,api_call,create_user):
        # reset the login state
        api_call.force_authenticate(user=None)
        
        user = create_user(username='AliStack')
        url = reverse('users:user-profile-mine')
        api_call.force_authenticate(user=user)
        response = api_call.get(url)
        
        # Check for returned user profile
        assert response.status_code == status.HTTP_200_OK
        
        payload = {'username':'Esteces'}
        response = api_call.patch(url,data=payload)
       
        assert response.status_code == status.HTTP_200_OK
        
    def test_change_password_user(self,api_call,create_user):
        # reset the login state
        api_call.force_authenticate(user=None)
        
        user = create_user()
        url = reverse('users:user-profile-new-password')
        api_call.force_authenticate(user=user)
        payload = {'new_password':'Stackpay09$','old_password':'Aliahmed091$'}
        response = api_call.patch(url,data=payload)
        
        assert response.status_code == status.HTTP_200_OK
    
    
@pytest.mark.django_db()
class TestVerificationCodeViewSet:
    def test_verify_user_code(self,api_call,create_user,email_code):
        # Verify with the active unused user code
        user = create_user()
        user_code = email_code(user=user)
        
        
        url = reverse('users:verify-code-validate')
        payload = {'email':user.email,'code':user_code.code}
        response = api_call.post(url,data=payload)
        
        user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_resend_verify_code(self,api_call,create_user,email_code):
        # Resend the code when the last one expired or was unreceived 
        user = create_user()
        email_code(user=user,expiry_time=timezone.now())
        
        url = reverse('users:verify-code-resend-code')
        response = api_call.post(url, data={'email': user.email})

        assert response.status_code == status.HTTP_200_OK, 'New verify code has send'