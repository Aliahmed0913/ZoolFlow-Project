from django.db import transaction as db_transaction
from transactions.models import Transaction
from transactions.services.paymob import PayMob, ProviderServiceError
import logging
logger = logging.getLogger(__name__)

def create_transaction(customer,validated_data):
    '''
    Create and return Transaction with provider PayMob
    '''
    logger.info(f"Creating transaction for customer {customer.id}, amount {validated_data['amount']}")
    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            customer=customer,
            **validated_data,
            )
    logger.info(f"Transaction {transaction.merchant_order_id} created successfully.")
    # Interact with provider to create order and payment token
    interact_with_provider(customer,transaction)
    transaction.refresh_from_db()
    return transaction

def interact_with_provider(customer,transaction:Transaction):
    '''
    Interact with PayMob to create order and payment key
    '''
    try:   
        merchant_id = transaction.merchant_order_id
        provider = PayMob(customer,merchant_id)
        amount_cents = int(transaction.amount*100)
        provider_id = provider.create_order(amount_cents)
        payment_token = provider.payment_key_token(provider_id=provider_id,amount_cents=amount_cents)
        # Update transaction with provider fields
        set_provider_fields(transaction,provider_id,payment_token)
    except ProviderServiceError as e:
        with db_transaction.atomic():
            tx = Transaction.objects.select_for_update().get(id=transaction.id)
            tx.state = Transaction.TransactionState.FAILED
            tx.save(update_fields=['state'])
        logger.warning(f"Transaction {merchant_id} failed during provider interaction: {e.message}")
        
    
def set_provider_fields(transaction,provider_id,payment_token):
    '''
    Set provider related fields in transaction instance
    '''
    with db_transaction.atomic():
        tx = Transaction.objects.select_for_update().get(id=transaction.id)
        tx.order_id = provider_id
        tx.payment_token = payment_token
        tx.state = Transaction.TransactionState.PENDING
        tx.save(update_fields=['order_id','payment_token','state'])
    logger.info(f'Transaction {tx.merchant_order_id} updated with provider fields.')