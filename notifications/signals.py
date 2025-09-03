from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save

from users.models import EmailCode
from notifications.services.verification_code import send_verification_code

@receiver(post_save, sender=EmailCode)
def handle_verify_code_mail(sender, instance, created, **kwargs):
    '''
    Listener to user verify code when any creation happen.
    
    it's mail that verify code'''
    if created :
        def on_commit():
            send_verification_code(instance.id)  # here where celery task is started
    
        transaction.on_commit(on_commit)