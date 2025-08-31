from rest_framework import status
from rest_framework.viewsets import ModelViewSet,GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from users.models import User
from users.serializers import UserRegistrationSerializer,UserProfileSerializer,EmailCodeVerificationSerializer,ChangePasswordSerializer
from users.services.verifying_code import VerificationCodeService, VerifyCodeStatus
from core.permissions.user import IsAdminOrOwner,IsAdmin
from notifications.services.verification_code import send_verification_code

# Create your views here.

class UserRegistrationView(APIView):
    throttle_scope = 'sign_up'
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        c_user = serializer.save()
        
        service = VerificationCodeService(c_user.id)
        code = service.create_code()
        send_verification_code(code.id) # here where celery task is started 
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserProfileViewSet(ModelViewSet):
    http_method_names = ['get','patch']
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = IsAuthenticated
    
    def get_permissions(self):
        if self.action in ['list','retrieve','partial_update']:
            return [IsAdmin()]
        return [IsAdminOrOwner()]
    
    def get_throttles(self):
        if self.action == 'change_password':
            self.throttle_scope = 'new_password'
        else:
            self.throttle_scope = 'profile'
        return super().get_throttles()
    
    
    @action(detail=False, methods=['GET','PATCH'],url_path='mine')
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
        
    @action(detail=False, methods=['PATCH'],url_path='mine/new-password') 
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'Password successfuly updated!'},status=status.HTTP_200_OK)
        

class VerificationCodeViewSet(GenericViewSet):
    serializer_class = EmailCodeVerificationSerializer
    verification_throttle_scope = {
        'verifying_user_code':'verify_code',
        'resend_user_code':'resend_code',
    }
    
    def get_throttles(self):
        self.throttle_scope = self.verification_throttle_scope.get(self.action, 'default')
        return super().get_throttles()
    
    @action(detail=False, methods=['POST'], url_path='validate')
    def verifying_user_code(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recived_code = serializer.validated_data.get('code')
        email = serializer.validated_data['email'] 
        
        user = self.get_user(email)

        if not recived_code:
            return Response({'code':'this field is required!'},status=status.HTTP_400_BAD_REQUEST)
        
        service = VerificationCodeService(user)
        result = service.validate_code(recived_code) 
              
        if result == VerifyCodeStatus.VALID:
            refresh_token = RefreshToken.for_user(user=user)
            return Response({
            'refresh':str(refresh_token),
            'access':str(refresh_token.access_token),
            },status=status.HTTP_200_OK)
        
        elif result == VerifyCodeStatus.IN_VALID:
            return Response({'code':'invalid code'},status=status.HTTP_400_BAD_REQUEST)
       
        elif result == VerifyCodeStatus.NOT_FOUND:
            return Response({'code':'not found'},status=status.HTTP_404_NOT_FOUND)
       
        return Response({'code':'expired!'},status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['POST'], url_path='resend')
    def resend_user_code(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        user = self.get_user(email)
        service = VerificationCodeService(user)
        code = service.recreate_code_on_demand()
        if code:
            send_verification_code(code.id)
            return Response({'code':'new verify code is send'},status=status.HTTP_200_OK)
        return Response({'code':'currently valid'})

    def get_user(self,email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFound({'error':f'invalid email'})

class CustomTokenObtainPairView(TokenObtainPairView):
    '''Customize token-generator to limit request per minute to 10'''
    throttle_scope = 'login'

