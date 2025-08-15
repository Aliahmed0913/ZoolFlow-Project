from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import UserSerializer 
from .models import User
from core.permissions.user import IsAdmin, IsOwner
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
# Create your views here.

class UserRegisterationViewset(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdmin ,IsOwner]
        return [permissions() for permissions in permission_classes]
    
    @action(detail=False, methods=['POST'],url_name='passowrd-change')
    def change_password(self, request):
        user = request.user
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': 'new Password required'},status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
