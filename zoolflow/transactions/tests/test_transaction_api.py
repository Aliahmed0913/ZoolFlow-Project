import pytest
from django.urls import reverse

from zoolflow.transactions.models import Transaction


@pytest.mark.django_db
class TestTransactionApi:
    def test_customer_sees_only_own_transactions(
        self, api_client, customer_factory
    ):
        customer_one = customer_factory(
            username="customer_one",
            email="customer_one@example.com",
            role_management="CUSTOMER",
        )
        customer_two = customer_factory(
            username="customer_two",
            email="customer_two@example.com",
            role_management="CUSTOMER",
        )

        Transaction.objects.create(customer=customer_one, amount=10)
        Transaction.objects.create(customer=customer_two, amount=20)

        api_client.force_authenticate(user=customer_one.user)
        response = api_client.get(reverse("transactions:transaction-list"))

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["amount"] == "10.00"

    def test_staff_can_list_all_transactions(
        self, api_client, customer_factory
    ):
        customer_one = customer_factory(
            username="staff_case_one",
            email="staff_case_one@example.com",
            role_management="CUSTOMER",
        )
        customer_two = customer_factory(
            username="staff_case_two",
            email="staff_case_two@example.com",
            role_management="CUSTOMER",
        )
        Transaction.objects.create(customer=customer_one, amount=30)
        Transaction.objects.create(customer=customer_two, amount=40)

        staff_customer = customer_factory(
            username="staff_user",
            email="staff_user@example.com",
            role_management="STAFF",
        )

        api_client.force_authenticate(user=staff_customer.user)
        response = api_client.get(reverse("transactions:transaction-list"))

        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_unverified_customer_cannot_create_transaction(
        self, api_client, customer_factory, mocker
    ):
        customer = customer_factory(
            username="unverified_customer",
            email="unverified_customer@example.com",
            role_management="CUSTOMER",
        )
        customer.is_verified = False
        customer.save(update_fields=["is_verified"])

        orchestrate_spy = mocker.patch(
            "zoolflow.transactions.views.TransactionOrchestrationService.create_transaction"
        )

        api_client.force_authenticate(user=customer.user)
        response = api_client.post(
            reverse("transactions:transaction-list"),
            {"amount": "120.00"},
            format="json",
        )

        assert response.status_code == 403
        assert not orchestrate_spy.called

    def test_idempotency_key_replays_existing_transaction(
        self, api_client, customer_factory, mocker
    ):
        customer = customer_factory(
            username="idempotent_customer",
            email="idempotent_customer@example.com",
            role_management="CUSTOMER",
        )
        customer.is_verified = True
        customer.save(update_fields=["is_verified"])
        existing = Transaction.objects.create(
            customer=customer,
            amount=120,
            idempotency_key="txn-key-001",
        )
        orchestrate_spy = mocker.patch(
            "zoolflow.transactions.views.TransactionOrchestrationService.create_transaction"
        )

        api_client.force_authenticate(user=customer.user)
        response = api_client.post(
            reverse("transactions:transaction-list"),
            {"amount": "120.00"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="txn-key-001",
        )

        assert response.status_code == 200
        assert response.data["merchant_order_id"] == existing.merchant_order_id
        assert not orchestrate_spy.called
