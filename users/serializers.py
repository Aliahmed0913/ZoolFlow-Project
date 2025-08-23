from rest_framework import serializers
from django.contrib.auth import get_user_model
from .validators import validate_password, validate_phone_number
from users.services.verifying_code import VerificationCodeService
from django.contrib.auth.hashers import check_password
from Restaurant.settings import CODE_LENGTH
import logging
logger = logging.getLogger(__name__)



User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
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
        return validate_password(value)
   
    def validate_phone_number(self, value):    
        return validate_phone_number(value)
        
    def create(self, validated_data):
        c_user = User.objects.create_user(**validated_data)
        service = VerificationCodeService(c_user)
        service.create_code()
        return c_user

class EmailCodeVerificationSerializer(serializers.Serializer):
        email = serializers.EmailField()
        code = serializers.CharField(required=False,max_length=CODE_LENGTH,min_length=CODE_LENGTH)
        
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