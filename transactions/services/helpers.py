import logging
from ..models import Transaction

logger = logging.getLogger(__name__)


def retrieve_transaction_for_update(**kwargs) -> Transaction | None:
    """
    Retrieve a copy of transaction with select_for_update,
    to avoid race conditions"""
    return Transaction.objects.select_for_update().filter(**kwargs).first()


def bring_transaction(**kwargs) -> Transaction | None:
    """Fetch transaction based on given kwargs"""
    transaction = Transaction.objects.filter(**kwargs)
    if not transaction.exists():
        id = (
            kwargs.get("transaction_id")
            if kwargs.get("transaction_id")
            else kwargs.get("merchant_order_id")
        )
        logger.warning(
            f"Transaction with id {id} doesn't exist.",
        )
        return None
    return transaction.first()
