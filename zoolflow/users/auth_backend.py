from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Override authenticate function that SimpleJWT design to work with. accept email either now.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        login = (username or kwargs.get("email") or "").strip()

        if not login or not password:
            return None

        try:
            user = User.objects.get(Q(username__iexact=login) | Q(email__iexact=login))
        except User.DoesNotExist:
            # run the password hasher to reduce response time (safty) measuring time
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
