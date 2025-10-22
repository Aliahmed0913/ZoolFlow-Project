from django.urls import path,include
from .views import UserProfileViewSet,VerificationCodeViewSet,UserRegistrationView,CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from rest_framework.routers import DefaultRouter

app_name = 'users' 

routers = DefaultRouter()
routers.register('profiles',UserProfileViewSet,basename='user-profile')
routers.register('verify-code',VerificationCodeViewSet, basename='verify-code')

urlpatterns = [ 
    path('',include(routers.urls)),
    path('sign-up/',UserRegistrationView.as_view(),name='registration'),
    path('login/',CustomTokenObtainPairView.as_view(),name='get-token'),
    path('refresh/',TokenRefreshView.as_view(),name='refresh-token'),
    path('logout/',TokenBlacklistView.as_view(),name='block-token'),
]
