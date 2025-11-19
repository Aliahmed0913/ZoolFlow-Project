
from django.urls import path, include
from customers.views import CustomerProfileAPIView,CustomerAddressViewSet, KnowYourCustomerAPIView
from rest_framework.routers import DefaultRouter

app_name = 'customers'

customer_address = DefaultRouter()
customer_address.register('address',CustomerAddressViewSet,basename='addresses')

urlpatterns =[
    path('profile/',CustomerProfileAPIView.as_view(),name='customer-profile'),
    path('',include(customer_address.urls),name='customer-address'),
    path('profile/upload-docs/',KnowYourCustomerAPIView.as_view(),name='kyc-docs'),
]
