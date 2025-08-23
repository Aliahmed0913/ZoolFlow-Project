from django.urls import path,include
from .views import UserProfileViewSet,VerificationCodeViewSet,UserRegistrationView,CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from rest_framework.routers import DefaultRouter


profile_update = DefaultRouter()
profile_update.register('profiles',UserProfileViewSet,basename='update-profile')

verify_code = DefaultRouter()
verify_code.register('verify-code',VerificationCodeViewSet, basename='verify-code')

urlpatterns = [
    path('',include(profile_update.urls)),
    path('',include(verify_code.urls)),
    
    path('sign-up/',UserRegistrationView.as_view(),name='registeration'),
    path('login/',CustomTokenObtainPairView.as_view(),name='get_token'),
    path('refresh/',TokenRefreshView.as_view(),name='refresh_token'),
    path('logout/',TokenBlacklistView.as_view(),name='block_token'),
]
