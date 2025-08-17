from django.urls import path,include
from .views import UserRegisterationViewset
from core.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from rest_framework.routers import DefaultRouter


profile_update = DefaultRouter()
profile_update.register('profiles',UserRegisterationViewset,basename='update-profile')

urlpatterns = [
    path('',include(profile_update.urls)),
    path('sign-up',UserRegisterationViewset.as_view({'post':'create'}),name='registeration'),
    path('login',CustomTokenObtainPairView.as_view(),name='get_token'),
    path('refresh-token',TokenRefreshView.as_view(),name='refresh_token'),
    path('logout',TokenBlacklistView.as_view(),name='block_token'),
]
