import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from config.settings import CODE_LENGTH
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailOrUsernameBackendSerializer(TokenObtainPairSerializer):
    # make simpleJWT accept email as input
    username_field = "email"


class UserRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role_management"]
        read_only_fields = ("is_active",)
        extra_kwargs = {
            "password": {"write_only": True},
            "is_active": {"default": False},
        }

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def validate_role_management(self, value):
        request = self.context.get("request")
        user = request.user

        if value in [User.Roles.ADMIN, User.Roles.STAFF]:
            if not user or not user.is_authenticated:
                raise serializers.ValidationError(
                    "Authentication required to create staff or admin users."
                )
            elif user.role_management != User.Roles.ADMIN:
                raise serializers.ValidationError(
                    "Only admins can assign admin or staff roles."
                )
        return value

    def create(self, validated_data):
        role = validated_data.get("role_management", User.Roles.CUSTOMER)
        is_staff = role in [User.Roles.ADMIN, User.Roles.STAFF]

        c_user = User.objects.create_user(
            **validated_data,
            is_active=False,  # will activated after success verification
            is_staff=is_staff,
        )
        return c_user


class EmailCodeVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=CODE_LENGTH, min_length=CODE_LENGTH)

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user is associated with this email.")
        return value

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "Verification code must contain only digits."
            )
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role_management", "email", "is_active"]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        request = self.context["request"]
        user_role = request.user.role_management
        if "role_management" in validated_data and user_role != User.Roles.ADMIN:
            logger.warning(f"{request.user.username} can't upgrade himself to admin")
            raise serializers.ValidationError(
                {"detail": "only admins can assign admin or staff roles"}
            )

        if "is_active" in validated_data and user_role != User.Roles.ADMIN:
            logger.warning(f"{user_role} can't activate himself")
            raise serializers.ValidationError(
                {"detail": "only admin can activate users"}
            )

        if "password" in validated_data:
            logger.warning("This endpoint can't update passwords")
            raise serializers.ValidationError(
                {"detail": "Use the change password endpoint to update passwords"}
            )

        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")

        if not check_password(old_password, user.password):
            raise serializers.ValidationError(
                {"old password": "Old password is incorrect"}
            )

        if check_password(new_password, user.password):
            raise serializers.ValidationError(
                {"new password": "New password must differ from old password"}
            )

        validate_password(new_password)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user
