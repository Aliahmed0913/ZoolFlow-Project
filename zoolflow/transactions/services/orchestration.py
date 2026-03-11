import logging
from django.db import transaction as db_transaction
from .paymob import PayMobClient, ProviderServiceError
from ..models import Transaction
from .helpers import retrieve_transaction_for_update

logger = logging.getLogger(__name__)


class TransactionOrchestrationServiceError(Exception):
    # Raised when orchestration handling fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class TransactionOrchestrationService:
    def __init__(self, customer):
        self.customer = customer

    def create_transaction(self, validated_data):
        """
        Create transaction with approbiate filed,
        after interacting with payment provider
        """
        logger.info(
            (
                f"Initiate transaction for customer with ID {self.customer.id} amount {validated_data['amount']}"
            ).replace("\n", "")
        )
        with db_transaction.atomic():
            transaction = Transaction.objects.create(
                customer=self.customer,
                **validated_data,
            )
        logger.info(
            (
                f"Transaction {transaction.merchant_order_id} created successfully."
            ).replace("\n", "")
        )
        # Interact with provider to create order and payment token on commit
        db_transaction.on_commit(
            lambda: self._interact_with_provider(transaction),
        )
        transaction.refresh_from_db()
        return transaction

    def _interact_with_provider(self, transaction: Transaction):
        """
        Interact with PayMob to create order and payment keym
        and set them in transaction passed object
        """
        merchant_id = transaction.merchant_order_id
        amount_cents = int(transaction.amount * 100)
        provider = PayMobClient(
            customer=self.customer,
            amount_cents=amount_cents,
        )
        try:
            # Create order and payment key token with provider
            # Return order id and payment token
            order_id = provider.create_order(merchant_id=merchant_id)
            payment_token = provider.payment_key_token(order_id=order_id)
            # Update transaction fields with provider returned values
            TransactionOrchestrationService._define_provider_attribute(
                transaction, order_id, payment_token
            )
        except ProviderServiceError as e:
            with db_transaction.atomic():
                tx = retrieve_transaction_for_update(id=transaction.id)
                if not tx:
                    raise TransactionOrchestrationServiceError(
                        "Transaction was not found while handling provider failure.",
                        details="Transaction",
                    )
                try:
                    tx.transition_to(Transaction.TransactionState.FAILED)
                except ValueError as exc:
                    raise TransactionOrchestrationServiceError(
                        str(exc),
                        details="Transition",
                    )
                tx.save(update_fields=["state"])
            logger.error(
                f"Transaction {merchant_id} failed during provider interaction: {e.message}"
            )
            raise TransactionOrchestrationServiceError(
                details="Provider interaction failed", message=e.message
            )

    @staticmethod
    def _define_provider_attribute(transaction, provider_id, payment_token):
        """
        Set provider related fields in transaction instance
        """
        with db_transaction.atomic():
            tx = retrieve_transaction_for_update(id=transaction.id)
            if not tx:
                raise TransactionOrchestrationServiceError(
                    "Transaction was not found while storing provider fields.",
                    details="Transaction",
                )
            tx.order_id = provider_id
            tx.payment_token = payment_token
            try:
                tx.transition_to(Transaction.TransactionState.PENDING)
            except ValueError as exc:
                raise TransactionOrchestrationServiceError(
                    str(exc),
                    details="Transition",
                )
            tx.save(update_fields=["order_id", "payment_token", "state"])
        logger.info(f"Transaction {tx.merchant_order_id} updated with provider fields.")

    @staticmethod
    def transaction_current_state(transaction_id):
        """
        Update transaction state with current state and sign ID (Transaction_ID)
        """

        current_data = PayMobClient().get_transaction_flags(transaction_id)
        # check fail at gateway level
        error_occured = current_data["error_occured"]
        if error_occured:
            return Transaction.TransactionState.ERROR
        # after earlier success voided and refunded can happen
        is_refunded = current_data["is_refunded"]
        is_voided = current_data["is_voided"]
        if is_refunded:
            return Transaction.TransactionState.REFUNDED
        elif is_voided:
            return Transaction.TransactionState.VOIDED

        is_success = current_data["success"]
        # 2-step pay auth->capture
        is_capture = current_data["is_capture"]
        is_auth = current_data["is_auth"]
        # 1-step pay
        is_standalone_payment = current_data["is_standalone_payment"]
        is_pending = current_data["pending"]
        if is_pending:
            return Transaction.TransactionState.PENDING
        elif is_success:
            if is_capture:
                return Transaction.TransactionState.SUCCEEDED
            elif is_auth:
                # need capture
                return Transaction.TransactionState.AUTHORIZED
            elif is_standalone_payment:
                return Transaction.TransactionState.SUCCEEDED
        return Transaction.TransactionState.FAILED

    @staticmethod
    def update_and_mail_state(merchant_id, transaction_id):
        """
        Update transaction id, state and forward these update to the user email
        """

        from zoolflow.notifications.tasks import transaction_state_email_task

        if not merchant_id or not transaction_id:
            raise TransactionOrchestrationServiceError(
                "Missing merchant_id or transaction_id in webhook payload.",
                details="Transaction",
            )

        state = TransactionOrchestrationService.transaction_current_state(
            transaction_id
        )
        with db_transaction.atomic():
            tx = retrieve_transaction_for_update(merchant_order_id=merchant_id)
            if not tx:
                raise TransactionOrchestrationServiceError(
                    f"Transaction {merchant_id} does not exist.",
                    details="Transaction",
                )

            is_same_state = tx.state == state
            is_same_provider_txn = str(tx.transaction_id) == str(transaction_id)
            if is_same_state and is_same_provider_txn:
                logger.warning(
                    f"Transaction {transaction_id} already processed with state {tx.state}",
                )
                return
            try:
                tx.transition_to(state)
            except ValueError as exc:
                raise TransactionOrchestrationServiceError(
                    str(exc),
                    details="Transition",
                )
            tx.transaction_id = transaction_id
            tx.save(update_fields=["state", "transaction_id"])
            logger.info(f"Transaction {tx.transaction_id} updated to {tx.state}.")
        db_transaction.on_commit(
            lambda: transaction_state_email_task.delay(transaction_id)
        )
