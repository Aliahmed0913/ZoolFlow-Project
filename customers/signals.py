from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User
from customers.models import KnowYourCustomer as KYC
from customers.services.start_customer import bootstrap_customer

import logging
logger = logging.getLogger(__name__)


@receiver(post_save,sender=User)
def handle_activation_user(sender, instance, created, **kwargs):
    '''
    Listen to users with role customer when it's successfully verified there email account
    
    instantiate an customer,address and KYC instances for that customer  
    '''
    if not created and instance.is_active and instance.role_management == 'CUSTOMER':
        if not hasattr(instance,'customer_profile'):
            bootstrap_customer(user=instance)

@receiver(post_save,sender=KYC)
def handle_approved_customer(sender, instance, created, **kwargs):
    '''
    Listen to the customer to get approved when the admin successfully emphasizes that the document is okay.   
    '''
    if not created:
        customer = instance.customer
        if instance.status_tracking == KYC.Status.APPROVED:
            customer.is_verified = True
            logger.info(f'{customer.full_name} has been verified successfully.')
        
        elif instance.status_tracking == KYC.Status.REJECTED :
            customer.is_verified = False
            logger.info('The document rejected.')
            
        else :
            customer.is_verified = False
            logger.info('Customer hasn\'t been verified yet')
        
        customer.save(update_fields=['is_verified'])