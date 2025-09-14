from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from users.models import User
from customers.models import Customer, Address, KnowYouCustomer

@receiver(post_save,sender=User)
def handle_activation_user(sender, instance, created, **kwargs):
    '''
    Listen to users with role customer when it's successfully verified there email account
    
    instantiate an customer instance represent there customer profile  
    '''
    if not created and instance.is_active and instance.role_management == 'CUSTOMER':
        if not hasattr(instance,'customer_profile'):
            Customer.objects.create(user = instance)


@receiver(post_save,sender=Customer)
def handle_customer_profile(sender, instance, created, **kwargs):
    '''
    Listen to customer creation to associated with address and KYC instances
    '''
    def on_commit():
        if created:
            Address.objects.create(customer=instance)
            KnowYouCustomer.objects.create(customer=instance)
    transaction.on_commit(on_commit)