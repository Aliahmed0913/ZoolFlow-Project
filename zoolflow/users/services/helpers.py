import logging
from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


logger = logging.getLogger(__name__)


def set_refresh_token_cookie(response: Response):
    """
    Set refresh token in the response cookie and cached response.

    :param response: Response object
    :param refresh_token: str, refresh token string
    """
    response.set_cookie(
        "refresh_token",
        response.data["refresh"],
        samesite=getattr(settings, "SESSION_COOKIE_SAMESITE", "Strict"),
        secure=getattr(settings, "SESSION_COOKIE_SECURE", False),
        httponly=getattr(settings, "SESSION_COOKIE_HTTPONLY", True),
        max_age=getattr(settings, "LIFETIME_SESSION", None),
    )
    logger.info({"users_helpers": "Refresh token has set in cookie."})
    return response


def get_token_from_cookie(request):
    """
    Return RefreshToken object if there an refresh token in the request cookie
    ,error message if one exist

    :param request: POST request usually
    """
    ref_token = request.COOKIES.get("refresh_token")
    if not ref_token:
        logger.warning({"users_helpers": "no refresh token in cookie"})
        return None, "No refresh token in cookie"
    try:
        refresh = RefreshToken(ref_token)
        logger.info({"users_helpers": "refresh token obtained from cookie"})
        return refresh, None
    except TokenError:
        logger.warning({"users_helpers": "invalid or expired refresh token in cookie"})
        return None, "invalid or expired refresh token"
