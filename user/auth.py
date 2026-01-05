import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .models import UserDevice

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for both Access and Refresh tokens
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith(f"{self.keyword} "):
            return None

        token = auth.split(" ")[1]

        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        device_id = payload.get("device_id")
        user_id = payload.get("user_id")

        if not device_id or not user_id:
            raise AuthenticationFailed("Invalid token payload")

        try:
            device = UserDevice.objects.select_related("user").get(
                user_id=user_id,
                id=device_id,
                is_active=True,
            )
        except UserDevice.DoesNotExist:
            raise AuthenticationFailed("Device revoked")

        current_ip = self._get_client_ip(request)
        device.update_device_ip(current_ip)

        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at"])

        return (device.user, payload)

        # token = None
        # token_type = "access"

        # token = self._get_access_token_from_request(request)

        # if not token:
        #     cookie_token = request.COOKIES.get("refresh")
        #     if cookie_token:
        #         token = cookie_token
        #         token_type = "refresh"

        # if not token:
        #     return None

        # try:
        #     payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # except jwt.ExpiredSignatureError:
        #     raise AuthenticationFailed("Token expired")
        # except jwt.InvalidTokenError:
        #     raise AuthenticationFailed("Invalid token")

        # payload = self._decode_token(token)
        # token_type = payload.get("type", token_type)

        # if token_type == "access":
        #     token_obj = self._get_access_token(payload)
        # else:
        #     token_obj = self._get_refresh_token(payload)

        # if not token_obj.is_valid():
        #     raise AuthenticationFailed("Token expired or invalid")

        # return (token_obj.user, token_obj)

    def _get_client_ip(self, request) -> str | None:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    # def _get_access_token_from_request(self, request) -> str | None:
    #     if hasattr(request, "data"):
    #         token_qs = request.data.get("access_token")
    #         if token_qs:
    #             return token_qs if not isinstance(token_qs, list) else token_qs[0]

    #     if hasattr(request, "META"):
    #         auth_header = authentication.get_authorization_header(request).decode(
    #             "utf-8"
    #         )
    #         if auth_header and auth_header.startswith(self.keyword):
    #             return auth_header[len(self.keyword) :].strip()
    #     return None

    # def _decode_token(self, token):
    #     try:
    #         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    #     except jwt.ExpiredSignatureError:
    #         raise AuthenticationFailed("Token has expired")
    #     except jwt.InvalidTokenError:
    #         raise AuthenticationFailed("Invalid token")
    #     return payload

    # def _get_access_token(self, payload) -> AccessToken|AuthenticationFailed:
    #     try:
    #         return AccessToken.objects.select_related("user").get(
    #             id=payload.get("id"), user_id=payload.get("user_id")
    #         )
    #     except AccessToken.DoesNotExist:
    #         raise AuthenticationFailed("Access token not found")

    # def _get_refresh_token(self, payload) -> RefreshToken|AuthenticationFailed:
    #     try:
    #         return RefreshToken.objects.select_related("user").get(
    #             id=payload.get("id"), user_id=payload.get("user_id")
    #         )
    #     except RefreshToken.DoesNotExist:
    #         raise AuthenticationFailed("Refresh token not found")

    # def authenticate_header(self, request):
    #     return self.keyword
