from rest_framework import serializers
from transactions.models import Transaction
from .services.transaction_orchestration import create_transaction
from .services.paymob import PayMobServiceError

class TransactionSerializer(serializers.ModelSerializer):
    class Meta():
        model = Transaction
        fields = ('customer','amount','status','paymob_order_id','paymob_payment_token','created_at')
        read_only_fields = ('customer','status','paymob_order_id','paymob_payment_token')
        extra_kwargs={
            'amount':{'required':True}
        }
    def validate_amount(self,value):
        if value <= 0:
            raise serializers.ValidationError('Invalid amount')
        return value
    
    def create(self, validated_data):
        # Customer always derived from request.user.customer_profile
        request = self.context.get('request')
        customer = request.user.customer_profile
        try:
        
            transaction = create_transaction(customer,validated_data)
            return transaction
        
        except PayMobServiceError as e:
            raise serializers.ValidationError({"non_field_errors":[f'{e.details}:{e.message}']})  
    