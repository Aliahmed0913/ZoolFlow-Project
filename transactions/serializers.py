from rest_framework import serializers
from transactions.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source='get_state_display',read_only=True)
    class Meta():
        model = Transaction
        fields = ('customer','transaction_id','amount','state','order_id','payment_token','created_at','state_display','merchant_order_id')
        read_only_fields = ('customer','transaction_id','state','order_id','payment_token','merchant_order_id')
        extra_kwargs={
            'amount':{'required':True}
        }
    def validate_amount(self,value):
        if value <= 0:
            raise serializers.ValidationError('Invalid amount')
        return value
    

    