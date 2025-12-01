from django.db import transaction as db_transaction
from transactions.models import Transaction
from transactions.services.paymob import PayMob
import logging
logger = logging.getLogger(__name__)

def create_transaction(customer,validated_data):
    '''
    Create and return Transaction async with PayMob
    
    '''
    amount_cents = int(validated_data.get('amount')*100)
    
    paymob = PayMob(customer)
    merchant_id = PayMob.generate_id()   
    paymob_id = paymob.create_order(merchant_id,amount_cents)
    payment_token = paymob.payment_key_token(paymob_id=paymob_id,amount_cents=amount_cents)
    
    logger.info(f"Creating transaction {merchant_id} for customer {customer.id}, amount {validated_data['amount']}")
    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            customer=customer,
            merchant_order_id = merchant_id,
            paymob_order_id = paymob_id,
            paymob_payment_token = payment_token,
            **validated_data,
            )
    logger.info(f"Transaction {merchant_id} created successfully.")
    return transaction