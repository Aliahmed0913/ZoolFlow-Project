from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password

import phonenumbers, logging 
from phonenumbers.phonenumberutil import NumberParseException
from Restaurant.settings import CODE_LENGTH

logger = logging.getLogger(__name__)

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    country = serializers.CharField(max_length=2, write_only=True, default=None)
    
    class Meta():
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'password','country']
        extra_kwargs={
            'password': {'write_only': True},
        }
    
    def validate_password(self, value):    
        validate_password(value,self.instance)
        return value 
    
    def validate_phone_number(self,value):
        country = self.initial_data.get('country')
        country = country.upper() if country else None
        try:
            phonenumber = phonenumbers.parse(value,country)
        
            if not phonenumbers.is_possible_number(phonenumber):
                raise serializers.ValidationError('Format is not possible')
        
            if not phonenumbers.is_valid_number(phonenumber):
                raise serializers.ValidationError('Not valid for specific region')
        
        except NumberParseException:
            raise serializers.ValidationError('Missing or invalid region or format')
        
        return str(phonenumbers.format_number(phonenumber,phonenumbers.PhoneNumberFormat.E164))

    def create(self, validated_data):
        validated_data.pop('country')  
        c_user = User.objects.create_user(**validated_data,
                                          is_active=False # will activated after success verification
                                          )
        return c_user

class EmailCodeVerificationSerializer(serializers.Serializer):
        email = serializers.EmailField()
        code = serializers.CharField(required=False,max_length=CODE_LENGTH,min_length=CODE_LENGTH)
    

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ['id', 'username', 'role_management', 'email', 'phone_number' , 'is_active']
        read_only_fields = ['id']
    
    def update(self, instance, validated_data):
        request = self.context['request']
        user_role = request.user.role_management
        if 'role_management' in validated_data and user_role != 'ADMIN':
            logger.warning(f'{request.user.username} can\'t upgrade himself to admin')
            raise serializers.ValidationError({'detail':'User can\'t upgrade himself to admin'})
        
        if 'is_active' in validated_data and user_role != 'ADMIN':
            logger.warning(f'{user_role} can\'t activate himself')
            raise serializers.ValidationError({'detail':'User can\'t activate himself'})
        
        if 'password' in validated_data:
            logger.warning('This endpoint can\'t update passwords')
            raise serializers.ValidationError({'detail':'Page can\'t handle password change.'})
        
        return super().update(instance, validated_data)
   
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = self.context['request'].user
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        
        if not check_password(old_password,user.password):
            raise serializers.ValidationError({'old password':'Old password incorrect'})
        
        if check_password(new_password,user.password):
            raise serializers.ValidationError({'new_password':'New password is identical to old password'})
        
        validate_password(new_password)
        return attrs
   
    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user