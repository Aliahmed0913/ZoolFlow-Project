import pytest
from ..services.webhook import WebhookService


@pytest.mark.django_db
class TestPayMobWebHookView:
    def test_recieved_hmac(self, api_client, mocker):
        mocker.patch(
            "zoolflow.transactions.services.webhook.bring_transaction",
            return_value=None,
        )
        recieved_hmac = (
            (
                "8cd9658e7234fe44365814fa53508c\
                06ea2a9076d073e471cc9bdcb53ac2d009f\
                d852e03218a47ab082a235b3f2e039f41a93\
                5b32e28bd12df151dd5708a97e5"
            )
            .replace(" ", "")
            .replace("\n", "")
        )
        payload = {
            "obj": {
                "pending": False,
                "id": 373906620,
                "amount_cents": 12353,
                "created_at": "2025-11-24T15:58:08.589528",
                "currency": "EGP",
                "error_occured": False,
                "has_parent_transaction": False,
                "integration_id": 5306007,
                "is_3d_secure": True,
                "is_auth": False,
                "is_capture": False,
                "is_refunded": False,
                "success": True,
                "is_standalone_payment": True,
                "is_voided": False,
                "order": {
                    "id": 422946804,
                    "merchant_order_id": "ORD-3E70A0",
                },
                "owner": 2045572,
                "source_data": {
                    "pan": "0008",
                    "type": "card",
                    "sub_type": "MasterCard",
                },
            }
        }
        webhook = WebhookService(
            data=payload["obj"],
            merchant_id="ORD-3E70A0",
            transaction_id="transaction_id_for_test",
        )

        try:
            webhook.verify_paymob_hmac(recieved_hmac)
        except Exception as e:
            pytest.fail(f"verify_paymob_hmac raised an exception: {e}")
