import jwt
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields import NullBooleanField
from rest_framework import authentication, exceptions

from .models import AccessToken, RefreshToken

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for both Access and Refresh tokens
    """

    keyword = "Bearer"

    def authenticate(self, request):
        token = None
        token_type = "access"

        token = self._get_access_token_from_request(request)

        if not token:
            cookie_token = request.COOKIES.get("refresh")
            if cookie_token:
                token = cookie_token
                token_type = "refresh"

        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        payload = self._decode_token(token)
        token_type = payload.get("type", token_type)

        if token_type == "access":
            token_obj = self._get_access_token(payload)
        else:
            token_obj = self._get_refresh_token(payload)

        if not token_obj.is_valid():
            raise exceptions.AuthenticationFailed("Token expired or invalid")

        return (token_obj.user, token_obj)

    def _get_access_token_from_request(self, request) -> str | None:
        if hasattr(request, "data"):
            token_qs = request.data.get("access_token")
            if token_qs:
                return token_qs if not isinstance(token_qs, list) else token_qs[0]

        if hasattr(request, "META"):
            auth_header = authentication.get_authorization_header(request).decode(
                "utf-8"
            )
            if auth_header and auth_header.startswith(self.keyword):
                return auth_header[len(self.keyword) :].strip()
        return None

    def _decode_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")
        return payload

    def _get_access_token(self, payload) -> AccessToken|exceptions.AuthenticationFailed:
        try:
            return AccessToken.objects.select_related("user").get(
                id=payload.get("id"), user_id=payload.get("user_id")
            )
        except AccessToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Access token not found")

    def _get_refresh_token(self, payload) -> RefreshToken|exceptions.AuthenticationFailed:
        try:
            return RefreshToken.objects.select_related("user").get(
                id=payload.get("id"), user_id=payload.get("user_id")
            )
        except RefreshToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Refresh token not found")

    def authenticate_header(self, request):
        return self.keyword
