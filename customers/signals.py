from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User
from customers.services.start_customer import bootstrap_customer

@receiver(post_save,sender=User)
def handle_activation_user(sender, instance, created, **kwargs):
    '''
    Listen to users with role customer when it's successfully verified there email account
    
    instantiate an customer,address and KYC instances for that customer  
    '''
    if not created and instance.is_active and instance.role_management == 'CUSTOMER':
        if not hasattr(instance,'customer_profile'):
            bootstrap_customer(user=instance)