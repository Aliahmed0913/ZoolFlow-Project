from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password

from users.validators import validate_phone
from Restaurant.settings import CODE_LENGTH

import logging
logger = logging.getLogger(__name__)

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    
    class Meta():
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'password','role_management']
        extra_kwargs={
            'password': {'write_only': True},
        }
    
    def validate_password(self, value):    
        validate_password(value,self.instance)
        return value 
    
    def validate_phone_number(self,value):
        return validate_phone(value)
    
    def validate_role_management(self,value):
        request = self.context.get('request')
        user = request.user
        if value in ['ADMIN','STAFF'] :
            if not user.is_authenticated:
                raise serializers.ValidationError('Authentication required to create staff or admin!')
            elif user.role_management != 'ADMIN':
                raise serializers.ValidationError('Only admin can assign admin or staff!')
        return value
    
    def update(self, instance, validated_data):
        # based on user role give the user access to admin site or not
        user_role = validated_data.get('role_management',instance.role_management)
        if user_role in ['ADMIN','STAFF']:
            instance.is_staff = True
        else:
            instance.is_staff = False
        return super().update(instance, validated_data)
    
    def create(self, validated_data):  
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