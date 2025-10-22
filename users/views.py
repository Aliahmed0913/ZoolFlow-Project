from rest_framework import status
from rest_framework.viewsets import ModelViewSet,GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import User
from users.serializers import UserRegistrationSerializer,UserProfileSerializer,EmailCodeVerificationSerializer,ChangePasswordSerializer
from users.services.verifying_code import VerificationCodeSerivce
from users.permissions import IsAdminOrOwner,IsAdmin, IsAdminOrStaff
from stackpay.settings import THROTTLES_SCOPE

# Create your views here.
class UserRegistrationView(APIView):
    throttle_scope = 'sign_up'
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data,context = {'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save() 
         
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserProfileViewSet(ModelViewSet):
    http_method_names = ['get','patch']
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list','retrieve']:
            return [IsAdminOrStaff()]
        elif self.action == 'partial_update':
            return [IsAdmin()]     
        return [IsAdminOrOwner()]
    
    def get_throttles(self):
        self.throttle_scope = THROTTLES_SCOPE.get(self.action,'profile')
        return super().get_throttles()
    
    @action(detail=False, methods=['GET','PATCH'],url_path='mine',url_name='mine')
    def my_profile(self,request):
        user = request.user
        data = request.data
        
        if request.method == 'PATCH':
            updated_user = self.get_serializer(user,data=data, partial=True)
            updated_user.is_valid(raise_exception=True)
            updated_user.save()
            return Response(updated_user.data, status=status.HTTP_200_OK)
        
        serialized_user = self.get_serializer(user)
        return Response(serialized_user.data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['PATCH'],url_path='mine/new-password',url_name='new-password') 
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'Message':'Password successfully updated.'},status=status.HTTP_200_OK)
        

class VerificationCodeViewSet(GenericViewSet):
    serializer_class = EmailCodeVerificationSerializer
    verification_throttle_scope = {
        'verifying_user_code':'verify_code',
        'resend_user_code':'resend_code',
    }
    
    def get_throttles(self):
        self.throttle_scope = THROTTLES_SCOPE.get(self.action, 'default')
        return super().get_throttles()
    
    @action(detail=False, methods=['POST'], url_path='validate',url_name='validate')
    def verifying_user_code(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recived_code = serializer.validated_data.get('code')
        email = serializer.validated_data['email'] 
        
        if not recived_code:
            return Response({'detail':'The code field is required.'},status=status.HTTP_400_BAD_REQUEST)
        
        service = VerificationCodeSerivce(email)
        result,user = service.validate_code(recived_code) 
              
        if result == service.VerifyCodeStatus.VALID:
            refresh_token = RefreshToken.for_user(user=user)
            return Response({
            'refresh':str(refresh_token),
            'access':str(refresh_token.access_token),
            },status=status.HTTP_200_OK)
       
        return Response({'detail':'The code has expired!'},status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['POST'], url_path='resend',url_name='resend-code')
    def resend_user_code(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        service = VerificationCodeSerivce(user_email=email)
        code = service.recreate_code_on_demand()
        
        if code == service.VerifyCodeStatus.CREATED:
            return Response({'Code':'A new verification code is sent'},status=status.HTTP_200_OK)
        elif code == service.VerifyCodeStatus.VALID:
            return Response({'detail':'The code is currently valid.'},status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Can\'t send code, user is verified.'},status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    '''Customize token-generator to limit request per minute to 10'''
    throttle_scope = 'login'
    

