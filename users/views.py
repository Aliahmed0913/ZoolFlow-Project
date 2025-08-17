from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from core.permissions.user import IsAdminOrOwner
from .serializers import UserSerializer 
from .models import User
from .services.user_profile import check_new_password
# Create your views here.

class UserRegisterationViewset(ModelViewSet):
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user_role = self.request.user.role_management
        users = User.objects.all()
        if user_role == 'ADMIN':
            return users
        return User.objects.none()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminOrOwner,IsAuthenticated]
        return [permissions() for permissions in permission_classes]
    
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
        username = request.user.username
        new_password = request.data.get('new_password')
       
        if not new_password:
            return Response({'Error': 'new_password field required'},status=status.HTTP_400_BAD_REQUEST)
        
        if check_new_password(self,new_password):
            return Response({'Message':f'Password successfuly updated for {username}'},status=status.HTTP_202_ACCEPTED)
        return Response({'Error':f'Password is identical to old.Please write new password!'},status=status.HTTP_400_BAD_REQUEST)

