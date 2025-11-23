import pytest
from django.urls import reverse
from django.test import override_settings
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status  
from customers.models import Customer, Address, KnowYourCustomer

@pytest.mark.django_db()
class TestCustomerProfileAPIView:
  def test_retrieve_profile(self,api_client,create_activate_user):
        # Only an authenticated user can show their profile
        url = reverse('customers:customer-profile')
        response = api_client.get(url,format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        user = create_activate_user(username='muthana',email='muthana0032@icloud.com')
        api_client.force_authenticate(user)
        response = api_client.get(url,format='json')
        assert response.status_code == status.HTTP_200_OK
       
    
  @pytest.mark.parametrize('payload,excepected_status',
                            [({'first_name':'Esteces',
                               'last_name':'balneces',
                               'phone_number':'+249902208587',
                               'dob':'2001-12-9',
                               },status.HTTP_200_OK),
                             ({'first_name':'steces',
                               'last_name':'balneces',
                               'phone_number':'249902208587',
                               'dob':'2020-11-9',
                               'is_verified':True},
                               status.HTTP_400_BAD_REQUEST)])
  def test_update_profile(self,api_client,payload,excepected_status,authenticate_client):
        # Only the customer user can update first_name, last_name, phone_number, and dob on their profile
        customer = Customer.objects.get(user=authenticate_client)
        url = reverse('customers:customer-profile')
        original_verified = customer.is_verified 
        response = api_client.patch(url,data=payload,format='json')
        
        assert response.status_code == excepected_status
        assert customer.is_verified == original_verified # The field (is_verified) is immutable by anyone except the admin
        
@pytest.mark.django_db()
class TestAddressViewSet:
  def test_valid_addresses(self,api_client,authenticate_client):
    url = reverse('customers:addresses-list')
    customer = Customer.objects.get(user=authenticate_client)
    payload = {'state':'daghuliail'
               ,'city':'mansoura'
               ,'line':'bn-ziad'
               ,'building_number':'14-a'
               ,'apartment_number':'a-33'
               ,'postal_code':'12345allid'
               }
    assert api_client.post(url,data=payload).status_code == status.HTTP_400_BAD_REQUEST
    
    payload = payload | {'postal_code':'12345'}
    response = api_client.post(url,data=payload)
    

    assert response.status_code == status.HTTP_201_CREATED
    
    address = Address.objects.get(id = response.data['id'])
    assert address.main_address == True
    
    
    last_address =  Address.objects.filter(customer=customer).order_by('-created_at').first()
    assert last_address.main_address # We have only one main address per customer
    
    url = reverse('customers:addresses-detail',args=[last_address.id])
    payload = {'main_address':False}
    response = api_client.patch(url,data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    
@pytest.mark.django_db()
class TestKnowYourCustomerAPIView:
  @pytest.mark.parametrize('file_name,file_size,content_type,status',[
                          ('ali_passport.pdf', 1 ,'application/pdf',status.HTTP_200_OK),
                          ('ali_passport.svg', 1024* 251,'image/svg+xml',status.HTTP_400_BAD_REQUEST),
                          ])
  def test_customer_docs(self,authenticate_client,api_client,file_name,file_size,content_type,status):
    with tempfile.TemporaryDirectory() as tmpdir:
      with override_settings(MEDIA_ROOT = tmpdir):
        url = reverse('customers:kyc-docs')
        file = SimpleUploadedFile(file_name,b'f'* file_size,content_type)   
        payload = {'document_type':KnowYourCustomer.DocumentType.NATIONAL_ID,
                   'document_id':'C01234T2',
                   'document_file':file}   
        response = api_client.patch(url,data=payload,format='multipart')
        assert response.status_code == status 

