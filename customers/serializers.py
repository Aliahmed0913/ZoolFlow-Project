from rest_framework import serializers
from pathlib import Path

from customers.models import Customer, Address, KnowYourCustomer
from stackpay.settings import DOCUMENT_SIZE,ADDRESSES_COUNT,STATE_LENGTH

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = Customer
        fields = ['user','first_name','last_name','phone_number','dob','is_verified']
        read_only_fields =['is_verified','user']
        extra_kwargs = {
            f : {'required':True} for f in ('first_name','last_name','phone_number','dob')
            }
    
class CustomerAddressSerializer(serializers.ModelSerializer):
    
    class Meta():
        model = Address
        fields = ['id','customer','country','state','city','line','building_nubmer','appartment_number','postal_code', 'main_address']
        read_only_fields = ['id','customer']
        extra_kwargs = {
            'main_address':{'default':True},
        }

    def get_fields(self):
        fields = super().get_fields()
        required_fields = ('state','city','line','building_nubmer','appartment_number','postal_code')
        for name in required_fields:
            if name in fields:
                fields[name].required = True
        return fields
    
    def validate_main_address(self,value):
        request = self.context.get('request')
        customer = request.user.customer_profile
        address_id = self.instance.id if self.instance else 0    
        #if user try to make no main address it will raise an error
        addresses = Address.objects.filter(customer_id = customer.id) 
        if not value:
            active_address = True if addresses.filter(main_address=True).exclude(id=address_id) else False  #fix
            if not active_address:
                raise serializers.ValidationError('Must at least have one main address')
       
        else:
            # reset all other main addresses to false if there new one true with query (update)
            addresses.filter(main_address=True).update(main_address=False)
        
        return value                        
            
    def validate_state(self, value):
        #must be more than STATE_LENGTH characters
        if len(value) <= STATE_LENGTH:
            raise serializers.ValidationError(f'Must be more than {STATE_LENGTH} character\'s')
        return value
    
    
    def create(self, validated_data):
        
        # add customer_id from the authentication access 
        request = self.context.get('request')
        customer = request.user.customer_profile
        validated_data['customer'] = customer
        
        # restrict the address table to have only 3 address per customer
        addresses = Address.objects.filter(customer = validated_data['customer'])
        is_able = True if addresses.count() < ADDRESSES_COUNT else False
        if not is_able:
            raise serializers.ValidationError({'Addresses':'You have reached maximum capacity'})
        
        return super().create(validated_data)
    
class KnowYourCustomerSerializer(serializers.ModelSerializer):
    class Meta():
        model = KnowYourCustomer
        fields = ['customer_id','document_type','document_id','document_file']
        read_only_fields = ('customer_id',)
        extra_kwargs = {
            f : {'required':True} for f in ('document_id','document_file')
        }
        
    def validate_document_file(self,value):
        # uploaded document size must be less than 250 KB
        if value.size > DOCUMENT_SIZE:
            raise serializers.ValidationError(detail=f'file too large. max size ({DOCUMENT_SIZE}) KB')
        
        # check that the uploaded file with types pdf/jpg
        extension = Path(value.name).suffix.lower()
        if extension not in ['.pdf','.jpg']:
            raise serializers.ValidationError(detail='file must be an pdf/jpg type')
        
        return value