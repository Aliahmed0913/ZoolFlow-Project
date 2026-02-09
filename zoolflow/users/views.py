from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
from django.conf import settings

from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.request import Request
from rest_framework.throttling import ScopedRateThrottle

from . import serializers
from .models import User
from .services.verifying_code import (
    VerificationCodeService,
    VerificationCodeServiceError,
    VerifyCodeStatus,
)
from .services.helpers import get_token_from_cookie, set_refresh_token_cookie
from .permissions import IsAdminOrOwner, IsAdmin, IsAdminOrStaff

# Create your views here.


class LoginThrottle(ScopedRateThrottle):
    scope = "login"


class LoginView(TemplateView):
    template_name = "zoolflow/users/templates/login.html"


# @method_decorator(csrf_protect, name="post")
class CookieTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]
    serializer_class = serializers.EmailOrUsernameBackendSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if getattr(response, "status_code", None) == 200 and "refresh" in response.data:
            response = set_refresh_token_cookie(response)
        return response


@method_decorator(csrf_protect, name="post")
class CookieTokenRefreshView(APIView):
    def post(self, request: Request):
        refresh, error_detail = get_token_from_cookie(request)
        if error_detail:
            return Response(
                {"detail": error_detail}, status=status.HTTP_401_UNAUTHORIZED
            )
        access = str(refresh.access_token)
        return Response({"access": access}, status=status.HTTP_200_OK)


class CookieTokenDisableTokenView(APIView):
    def post(self, request: Request):
        refresh, error_detail = get_token_from_cookie(request)
        if error_detail:
            return Response(
                {"detail": error_detail}, status=status.HTTP_401_UNAUTHORIZED
            )
        refresh.blacklist()
        response = Response(
            {"detail": "token disabled"},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("refresh_token")
        return response


class UserRegistrationView(APIView):
    throttle_scope = "sign_up"

    def post(self, request):
        serializer = serializers.UserRegistrationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserProfileViewSet(ModelViewSet):
    http_method_names = ["get", "patch"]
    serializer_class = serializers.UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAdminOrStaff()]
        elif self.action == "partial_update":
            return [IsAdmin()]
        return [IsAdminOrOwner()]

    def get_throttles(self):
        scope = getattr(settings, "THROTTLES_SCOPE", {})
        self.throttle_scope = scope.get(self.action, "profile")
        return super().get_throttles()

    @action(detail=False, methods=["GET", "PATCH"], url_path="mine", url_name="mine")
    def my_profile(self, request):
        user = request.user
        data = request.data

        if request.method == "PATCH":
            updated_user = self.get_serializer(user, data=data, partial=True)
            updated_user.is_valid(raise_exception=True)
            updated_user.save()
            return Response(updated_user.data, status=status.HTTP_200_OK)

        serialized_user = self.get_serializer(user)
        return Response(serialized_user.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["PATCH"],
        url_path="mine/new-password",
        url_name="new-password",
    )
    def change_password(self, request):
        serializer = serializers.ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password successfully updated."},
            status=status.HTTP_200_OK,
        )


class VerificationCodeViewSet(GenericViewSet):
    serializer_class = serializers.EmailCodeVerificationSerializer

    def get_throttles(self):
        self.throttle_scope = getattr(settings, "THROTTLES_SCOPE", {}).get(
            self.action, "verify_code"
        )
        return super().get_throttles()

    @action(detail=False, methods=["POST"], url_path="validate", url_name="validate")
    def verifying_user_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        received_code = serializer.validated_data.get("code")
        email = serializer.validated_data["email"]

        service = VerificationCodeService(email)
        try:
            result, user = service.validate_code(received_code)

            if result == VerifyCodeStatus.VALID:
                refresh_token = RefreshToken.for_user(user=user)
                response = Response(
                    {
                        "refresh": str(refresh_token),
                        "access": str(refresh_token.access_token),
                    },
                    status=status.HTTP_200_OK,
                )
                response = set_refresh_token_cookie(response)
                return response
        except VerificationCodeServiceError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["POST"], url_path="resend", url_name="resend-code")
    def resend_user_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        verify_code = VerificationCodeService(email)
        result = verify_code.recreate_code_on_demand()

        if result == VerifyCodeStatus.CREATED:
            return Response(
                {"detail": "New verification code sent."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Failed to send verification code."},
            status=status.HTTP_400_BAD_REQUEST,
        )
