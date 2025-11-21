from customers.models import Customer, Address, KnowYourCustomer
from django.db import transaction

@transaction.atomic
def bootstrap_customer(user):
    customer = Customer.objects.create(user = user)
    Address.objects.create(customer=customer,main_address=True)
    KnowYourCustomer.objects.create(customer=customer)
    return True