from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source="get_state_display", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "customer",
            "transaction_id",
            "merchant_order_id",
            "order_id",
            "amount",
            "state_display",
            "created_at",
        )
        read_only_fields = (
            "customer",
            "transaction_id",
            "order_id",
            "merchant_order_id",
        )
        extra_kwargs = {"amount": {"required": True}}

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Invalid amount")
        return value
