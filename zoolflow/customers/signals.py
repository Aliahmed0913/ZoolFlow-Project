import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import KnowYourCustomer as KYC
from .services.helpers import initialize_customer
from zoolflow.users.models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def handle_customer_creation(sender, instance, created, **kwargs):
    """
    Listen to users with role customer when it's successfully verified there email account

    instantiate an customer,address and KYC instances for that customer
    """
    if not created and instance.is_active and instance.role_management == "CUSTOMER":
        if not hasattr(instance, "customer_profile"):
            initialize_customer(user=instance)
            logger.info("Customer and all references set up.")


@receiver(post_save, sender=KYC)
def handle_kyc_status_change(sender, instance, created, **kwargs):
    """
    Listen to the customer to get approved when the admin successfully emphasizes that the document is okay.
    """
    if not created:
        customer = instance.customer
        if instance.status_tracking == KYC.Status.APPROVED:
            customer.is_verified = True
            logger.info(f"{customer.user.email} has been verified successfully.")

        elif instance.status_tracking == KYC.Status.REJECTED:
            customer.is_verified = False
            logger.info("The document has been rejected.")

        else:
            customer.is_verified = False
            logger.info("Pending")

        customer.save(update_fields=["is_verified"])
