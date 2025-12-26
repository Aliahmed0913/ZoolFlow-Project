from django.db import transaction as db_transaction
from transactions.models import Transaction
from transactions.services.paymob import PayMob, ProviderServiceError
import logging
logger = logging.getLogger(__name__)

def create_transaction(customer,validated_data):
    '''
    Create and return Transaction with provider PayMob
    
    '''
    provider = PayMob(customer)
    amount_cents = int(validated_data.get('amount')*100)
    merchant_id = validated_data['merchant_order_id']
    
    logger.info(f"Creating transaction for customer {customer.id}, amount {validated_data['amount']}")
    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            customer=customer,
            merchant_order_id=merchant_id,
            **validated_data,
            )
    logger.info(f"Transaction {merchant_id} created successfully.")
    
    # Interact with provider to create order and payment token
    interact_with_provider(merchant_id,amount_cents,provider,transaction)
    return transaction

def interact_with_provider(merchant_id,amount_cents,provider,transaction):
    '''
    Interact with PayMob to create order and payment key
    '''
    try:   
        provider_id = provider.create_order(merchant_id,amount_cents)
        payment_token = provider.payment_key_token(provider_id=provider_id,amount_cents=amount_cents)
        # Update transaction with provider fields
        set_provider_fields(transaction,merchant_id,provider_id,payment_token)
    except ProviderServiceError as e:
        transaction.state = Transaction.TransactionState.FAILED
        transaction.save(update_fields=['state'])
        logger.warning(f"Transaction {merchant_id} failed during provider interaction: {e.message}")
        raise
    
def set_provider_fields(transaction,merchant_id,provider_id,payment_token):
    '''
    Set provider related fields in transaction instance
    '''
    transaction.merchant_order_id = merchant_id
    transaction.order_id = provider_id
    transaction.payment_token = payment_token
    transaction.state = Transaction.TransactionState.PENDING
    transaction.save(update_fields=['merchant_order_id','order_id','payment_token','state'])
    logger.info(f'Transaction {merchant_id} updated with provider fields.')