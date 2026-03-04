import pytest
from django.db import transaction as db_transaction
from ..services.orchestration import TransactionOrchestrationService as tos


@pytest.mark.django_db
def test_orchestration_transaction(mocker, customer_factory):
    validated_data = {"amount": 100.22}
    customer = customer_factory()
    # replace paymob class with mock to prevent actual calls
    mock_paymob = mocker.patch(
        "zoolflow.transactions.services.orchestration.PayMobClient",
    )
    # configure mock methods and return values
    instance = mock_paymob.return_value
    instance.create_order.return_value = "paymob-id2232"
    instance.payment_key_token.return_value = (
        "test-paymob-token-in-transaction-creation"
    )
    # ensure on_commit calls are executed immediately
    mocker.patch.object(
        db_transaction,
        "on_commit",
        lambda func: func(),
    )
    # call the provider orchestration function
    orchestration = tos(customer=customer)
    transaction = orchestration.create_transaction(validated_data)
    assert instance.payment_key_token.called
    assert transaction.customer == customer
    assert transaction.order_id == "paymob-id2232"
    assert transaction.payment_token == "test-paymob-token-in-transaction-creation"
