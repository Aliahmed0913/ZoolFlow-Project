from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailCode
from .services.verifying_code import create_email_code
import re, logging
logger = logging.getLogger(__name__)

PASSWORD_REGEX = re.compile(r'^[A-Z](?=.*[a-z])(?=.*\d)(?!.*\s).{7,14}$')
PHONE_NUMBER_REGEX = re.compile(r'^(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*$')

user = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = user
        fields = ['id', 'username', 'role_management', 'email', 'phone_number', 'password' , 'is_active']
        extra_kwargs={
            'password': {'write_only': True},
            'is_active':{'read_only': True}
        }
    
    def update(self, instance, validated_data):
        request = self.context['request']
        if 'role_management' in validated_data:
            user_role = validated_data['role_management']
            if user_role == 'ADMIN' and request.user.role_management != 'ADMIN':
                validated_data.pop('role_management')
                logger.warning(f'{request.user.username} can\'t upgrade herself to admin')
            
        if 'password' in validated_data:
            validated_data.pop('password')
            logger.warning('This endpoint can\'t update passwords')
            
        return super().update(instance, validated_data)
    
    def validate_password(self, value):    
        if not PASSWORD_REGEX.fullmatch(value):
            raise serializers.ValidationError({'Error':'Password must be alphanumeric start with uppercase ,'
                                              'restricted in (8,15) character'})
        return value
   
    def validate_phone_number(self, value):    
        if not PHONE_NUMBER_REGEX.fullmatch(value):
            raise serializers.ValidationError('only allowing for an international dialing code at the start, - and spaces')
        return value
        
    def create(self, validated_data):
        c_user = user.objects.create_user(**validated_data)
        create_email_code(c_user)
        return c_user

class EmailCodeSerializer(serializers.ModelSerializer):
    class Meta():
        model = EmailCode
        fields = '__all__'
        read_only_fields = '__all__'