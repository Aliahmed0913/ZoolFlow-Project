from rest_framework import serializers
from pathlib import Path
from customers.models import Customer, Address, KnowYourCustomer
from stackpay.settings import DOCUMENT_SIZE,ADDRESSES_COUNT,STATE_LENGTH

import logging
logger = logging.getLogger()

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
        fields = ['id','customer','country','state','city','line','building_number','appartment_number','postal_code', 'main_address']
        read_only_fields = ['id','customer']
        extra_kwargs = (
            {f :{'required':True} for f in ('state','city','line','building_number','appartment_number','postal_code')}
            | {'main_address': {'default':True}}
            )
            
    def validate_state(self, value):
        # must be more than STATE_LENGTH characters
        if len(value) <= STATE_LENGTH:
            logger.warning(f'State length must be equal to or more than {STATE_LENGTH} characters')
            raise serializers.ValidationError(f'Must be more than {STATE_LENGTH} characters')
        return value
    
    def _enforce_main_address(self,customer,value,instance=None):
        '''
        The rule for the main address field ensures the existence of at least one main address and no duplication of it.
        '''
        addresses = Address.objects.filter(customer = customer) 
        #if user try to make no main address it will raise an error        
        if not value:
            has_another_main = addresses.filter(main_address=True).exclude(id=instance.id).exists() if instance else addresses.filter(main_address=True).exists()
            if not has_another_main:
                logger.warning('Must at least have one main address')
                raise serializers.ValidationError('Must at least have one main address')
        else:
            # reset all other main addresses to false if there new one true with query (update)
            addresses.filter(main_address=True).update(main_address=False)
            
    def update(self, instance, validated_data):
         #if user try to make no main address it will raise an error
        if 'main_address' in validated_data:   
             self._enforce_main_address(instance.customer,validated_data['main_address'],instance)
        return super().update(instance, validated_data)        
    
    def create(self, validated_data):
        
        # add customer_id from the request  
        request = self.context.get('request')
        customer = getattr(request.user,'customer_profile')
        if not customer:
            raise serializers.ValidationError('Customer profile not found.')
        
        validated_data['customer'] = customer
        
        # Restrict the address table to have only 3 addresses per customer
        addresses = Address.objects.filter(customer = validated_data['customer'])
        if addresses.count() >= ADDRESSES_COUNT:
            logger.warning(f'A customer can have a maximum of {ADDRESSES_COUNT} addresses')
            raise serializers.ValidationError({'Addresses':'You have reached maximum capacity'})
        
        self._enforce_main_address(customer,validated_data['main_address'])
        
        
        return super().create(validated_data)
    
class KnowYourCustomerSerializer(serializers.ModelSerializer):
    class Meta():
        model = KnowYourCustomer
        fields = ['customer_id','document_type','document_id','document_file']
        read_only_fields = ('customer_id',)
        extra_kwargs = {
            f : {'required':True} for f in ('document_type','document_id','document_file')
        }
        
    def validate_document_file(self,value):
        # uploaded document size must be less than 250 KB
        if value.size > DOCUMENT_SIZE:
            logger.warning('File size is too big')
            raise serializers.ValidationError(detail=f'file too large. max size {DOCUMENT_SIZE}KB')
        
        # check that the uploaded file with types pdf/jpg
        extension = Path(value.name).suffix.lower()
        if extension not in ['.pdf','.jpg']:
            logger.warning('File type isn\'t supported')
            raise serializers.ValidationError(detail='file must be an pdf/jpg type')
        
        return value
    