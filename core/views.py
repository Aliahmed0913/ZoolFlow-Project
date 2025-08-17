from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
# Create your views here.

#Customize token-generator to limit request per minute to 10
class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_scope = 'login'