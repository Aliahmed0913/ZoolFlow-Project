from rest_framework.serializers import ModelSerializer
from customers.models import Customer
from customers.validators import validate_phone,valid_age

class CustomerProfileSerializer(ModelSerializer):
    class Meta():
        model = Customer
        fields = ['user','full_name','phone_number','country','dob','is_verified']
        read_only_fields =['is_verified','user']
        
    def validate_phone_number(self,value):
        return validate_phone(value)
    
    def validate_dob(self,value):
        return valid_age(value)