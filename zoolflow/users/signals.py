from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import User
from .services.verifying_code import VerificationCodeService


@receiver(post_save, sender=User)
def initiate_verification_code(sender, instance, created, **kwargs):
    """
    Listener to user when any registeration event happen.

    it's create an verify code"""
    if created:

        def on_commit():
            service = VerificationCodeService(instance.email)
            service.create_verification_code()

        transaction.on_commit(on_commit)
