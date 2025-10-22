
from django.urls import path, include
from customers.views import CustomerProfileAPIView,CustomerAddressViewSet, KnowYourCustomerAPIView
from rest_framework.routers import DefaultRouter

app_name = 'customers'

customer_address = DefaultRouter()
customer_address.register('address',CustomerAddressViewSet,basename='customer_address')

urlpatterns =[
    path('',include(customer_address.urls)),
    path('profile/',CustomerProfileAPIView.as_view()),
    path('profile/upload-docs/',KnowYourCustomerAPIView.as_view()),
]
