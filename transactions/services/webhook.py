import logging
from transactions.models import Transaction as T
import hashlib,hmac

logger = logging.getLogger(__name__)
def handle_webhook(merchant_id,success):
    try:
        transaction = T.objects.get(merchant_order_id=merchant_id)
        transaction.status = T.TransactionStatus.SUCCESS if success else T.TransactionStatus.FAILED
        transaction.save(update_fields=['status'])
        logger.info(f'Transaction {merchant_id} updated to {transaction.status}')
    except T.DoesNotExist:
        logger.warning(f'webhook for unknown {merchant_id}')
              
HMAC_SECRET_KEY = 'A75D2BFFB4EEECC7C796318B5C5EFBB7'
def verify_hmac(received_hmac,data):
    concatenate_fields = str.join('',[
            str(data['amount_cents']),
            str(data['created_at']),  
            str(data['currency']),    
            str(data['error_occured']).lower(),
            str(data['has_parent_transaction']).lower(),
            str(data['id']),
            str(data['integration_id']),
            str(data['is_3d_secure']).lower(),
            str(data['is_auth']).lower(),
            str(data['is_capture']).lower(),
            str(data['is_refunded']).lower(),
            str(data['is_standalone_payment']).lower(),
            str(data['is_voided']).lower(),
            str(data['order']['id']),
            str(data['owner']),
            str(data['pending']).lower(),
            str(data['source_data']['pan']),
            str(data['source_data']['sub_type']),
            str(data['source_data']['type']),
            str(data['success']).lower(),
    ])
    
    encode_key,encode_fields = HMAC_SECRET_KEY.encode('utf-8'),concatenate_fields.encode('utf-8')
    calculate_hmac = hmac.new(encode_key,encode_fields,digestmod=hashlib.sha512).hexdigest()
    
    if not (hmac.compare_digest(calculate_hmac,received_hmac)):
        logger.warning('This callback doesn\'t belong to this process.')
        return False
    logger.info('HMAC verified success.')
    return True
    