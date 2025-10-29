import pytest
from customers.models import Customer, Address, KnowYourCustomer
from django.urls import reverse
from rest_framework import status  
@pytest.mark.django_db()   # continue here work
def test_activate_customer_signal(create_activate_user,mock_mail):
    # this signal takecare of creating an customer-profile, address, KYC instance.
    # all reference to that user
    
    user = create_activate_user()
    customer = Customer.objects.get(user=user)
    
    assert customer
    assert KnowYourCustomer.objects.filter(customer_id=customer.id).exists()
    assert Address.objects.filter(customer_id=customer.id).exists()

# @pytest.mark.django_db()
# def test_customer_address(create_activate_user,api_client,mock_mail):
#     user = create_activate_user()
#     path = reverse('customers:addresses-list')
#     payload = {
#         'state':'cairo','city':'al-haram','line':'tersa','building_nubmer':'14',
#         'appartment_number':'13-b','postal_code':'12345'
#     }
#     api_client.force_authenticate(user=user)
#     response = api_client.post(path,data=payload)
#     response = api_client.post(path,data=payload)
#     assert response.status_code == status.HTTP_201_CREATED
    
    # response = api_client.post(path,data=payload)
    # assert response.status_code == status.HTTP_201_CREATED
    
    
    # assert customer == Customer.objects.get(user=response_c.data['user'])
    
    
    
    # response_ad = api_client.get(path)
    # address = Address.objects.filter(customer=response_c.data['customer'])
    # response_k = api_client.get(path)
    # kyc = KnowYourCustomer.objects.get(customer=response_k.data['customer'])
    
    