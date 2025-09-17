from rest_framework import serializers
from customers.models import Customer, Address
from customers.validators import validate_phone,valid_age

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = Customer
        fields = ['user','full_name','phone_number','country','dob','is_verified']
        read_only_fields =['is_verified','user']
        extra_kwargs = {
            f : {'required':True} for f in ('full_name','phone_number','dob')
            }
        
        
    def validate_phone_number(self,value):
        return validate_phone(value)
    
    def validate_dob(self,value):
        return valid_age(value)
    
ADDRESSES_COUNT = 3
STATE_LENGTH = 3
class CustomerAddressSerializer(serializers.ModelSerializer):
    
    class Meta():
        model = Address
        fields = ['id','customer', 'line', 'state', 'appartment_number', 'main_address']
        read_only_fields = ['customer']
        extra_kwargs = {
            'main_address':{'default':True},
        }

    def get_fields(self):
        fields = super().get_fields()
        required_fields = ('line', 'state', 'appartment_number')
        for name in required_fields:
            if name in fields:
                fields[name].required = True
        return fields
    
        
    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        
        # add customer_id from the authentication access 
        customer = request.user.customer_profile
        attrs['customer'] = customer
        
        # state validation 
        state = str(attrs.get('state'))
        
        #must be more than 3 characters
        if len(state) <= STATE_LENGTH:
            raise serializers.ValidationError({'state':f'Must be more than {STATE_LENGTH} character\'s'})
        
        # main_address validation
        main_address = attrs.get('main_address') or self.instance.main_address
        
        #if user try to make no main address it will raise an error 
        if not main_address:
            active_address = True if Address.objects.filter(customer_id=customer.id,main_address=True).first() else False
            if not active_address:
                raise serializers.ValidationError({'Addresses':'Must at least have one main address'})
       
        else:
            # reset all other main addresses to false if there new one true with query (update)
            Address.objects.filter(customer_id = attrs.get('customer_id')).update(main_address=False)
        
            
        return attrs
    
    def create(self, validated_data):
        # restrict the address table to have only 3 address per customer
        addresses = Address.objects.filter(customer = validated_data.get('customer'))
        is_able = True if addresses.count() < ADDRESSES_COUNT else False
        if not is_able:
            raise serializers.ValidationError({'Addresses':'You have reached maximum capacity'})
        
        return super().create(validated_data)