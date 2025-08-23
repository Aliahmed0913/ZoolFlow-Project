from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet,GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle,AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from core.permissions.user import IsAdminOrOwner
from .serializers import UserSerializer,EmailCodeVerificationSerializer,ChangePasswordSerializer
from .models import User

from users.services.verifying_code import VerificationCodeService, VerifyCodeStatus
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.views import TokenObtainPairView
# Create your views here.

class UserRegistrationView(APIView):
    throttle_scope = 'sign_up'
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserProfileViewSet(ModelViewSet):
    serializer_class = UserSerializer
    http_method_names = ['get','patch']
    permission_classes = [IsAdminOrOwner,IsAuthenticated]
    
    def get_throttles(self):
        if self.action == 'change_password':
            self.throttle_scope = 'new_password'
        else:
            self.throttle_scope = 'profile'
        return super().get_throttles()
    
    def get_queryset(self):
        user_role = self.request.user.role_management
        users = User.objects.all()
        if user_role == 'ADMIN':
            return users
        return User.objects.none()
    
    @action(detail=False, methods=['GET','PATCH'],url_path='mine')
    def my_profile(self,request):
        user = request.user
        data = request.data
        
        if request.method == 'PATCH':
            updated_user = self.get_serializer(user,data=data, partial=True)
            updated_user.is_valid(raise_exception=True)
            updated_user.save()
            return Response(updated_user.data, status=status.HTTP_202_ACCEPTED)
        
        serialized_user = self.get_serializer(user)
        return Response(serialized_user.data)
        
    @action(detail=False, methods=['PATCH'],url_path='mine/new-password') 
    def change_password(self, request):
        #serializerfor password
        serializer = ChangePasswordSerializer(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':f'Password successfuly updated'},status=status.HTTP_200_OK)
        


class VerificationCodeViewSet(GenericViewSet):
    serializer_class = EmailCodeVerificationSerializer
    def get_throttles(self):
        if self.action == 'verifying_user_code':
            self.throttle_scope = 'verify_code'
        else:
             self.throttle_scope = 'resend_code'
        return super().get_throttles()
    
    @action(detail=False, methods=['POST'], url_path='validate')
    def verifying_user_code(self,request):
       
       
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recived_code = serializer.validated_data['code']
        email = serializer.validated_data['email'] 
        user = self.get_user(email)

        if not recived_code:
            return Response({'error':'verify code field is required!'},status=status.HTTP_400_BAD_REQUEST)
        
        service = VerificationCodeService(user)
        result = service.validate_code(recived_code) 
              
        if result == VerifyCodeStatus.VALID:
            refresh_token = RefreshToken.for_user(user=user)
            return Response({
            'refresh':str(refresh_token),
            'access':str(refresh_token.access_token),
            },status=status.HTTP_201_CREATED)
        
        elif result == VerifyCodeStatus.IN_VALID:
            return Response({'error':'invalid code'},status=status.HTTP_400_BAD_REQUEST)
       
        elif result == VerifyCodeStatus.NOT_FOUND:
            return Response(f'{user.username} doesn\'t have an active code',status=status.HTTP_404_NOT_FOUND)
       
        return Response({'error':'user code is expired!'},status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['POST'], url_path='resend')
    def resend_user_code(self,request):

        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        user = self.get_user(email)
        service = VerificationCodeService(user)
        
        if service.recreate_code_on_demand():
            return Response('new verify code is send',status=status.HTTP_200_OK)
        return Response('your current verify code is valid.',status=status.HTTP_200_OK)

    def get_user(self,email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFound({'error':f'user with email {email} does\'t exist!'})


class CustomTokenObtainPairView(TokenObtainPairView):
    '''Customize token-generator to limit request per minute to 10'''
    throttle_scope = 'login'

