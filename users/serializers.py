from rest_framework import serializers
from .models import User
import re

PASSWORD_REGEX = re.compile(r'^[A-Z](?=.*[a-z])(?=.*\d)(?!.*\s).{7,14}$')
PHONE_NUMBER_REGEX = re.compile(r'^(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*$')

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ['id', 'username', 'role_management', 'email', 'phone_number', 'password']
        extra_kwargs={
            'password': {'write_only': True}
        }
    
    def validate_password(self, value):    
        if not PASSWORD_REGEX.fullmatch(value):
            raise serializers.ValidationError('Password must be alphanumeric start with uppercase ,'
                                              'restricted in (8,15) character')
        return value
   
    def validate_phone_number(self, value):    
        if not PHONE_NUMBER_REGEX.fullmatch(value):
            raise serializers.ValidationError('only allowing for an international dialing code at the start, - and spaces')
        return value
        
    
    