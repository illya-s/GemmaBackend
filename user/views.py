"""
# user/views.py

# pyright: ignore[reportMissingTypeStubs]
"""

import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import JWTAuthentication
from .models import AccessToken, RefreshToken
from .serializers import (
    AccessTokenSerializer,
    EnterCodeSerializer,
    RequestCodeSerializer,
)
from .utils import send_login_code


class RequestCodeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RequestCodeSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        login_code = serializer.save()

        try:
            send_login_code(email=login_code.get("email"), code=login_code.get("code"))
            return Response(
                {"message": "Код отправлен на email"},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EnterCodeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EnterCodeSerializer

    def post(self, request: Request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        user = result["user"]

        res = Response(
            {
                "message": "Вы вошли!",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar.url if user.avatar else None,
                },
                "access_token": result["access_token"],
            },
            status=status.HTTP_200_OK,
        )
        res.set_cookie(
            key="refresh",
            value=result["refresh_token"],
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            secure=settings.SESSION_COOKIE_SECURE,
            domain=settings.SESSION_COOKIE_DOMAIN,
        )
        return res


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        user = request.user
        return Response(
            {
                "id": user.pk,
                "uid": user.uid,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar.url if user.avatar else None,
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    """
    POST /auth/refresh/
    {
        "refresh": "<refresh_token>"
    }
    """

    authentication_classes = [JWTAuthentication]

    def post(self, request: Request):
        refresh_token_str = request.COOKIES.get("refresh")

        if not refresh_token_str:
            return Response({"detail": "Missing refresh token"}, status=400)

        try:
            payload = JWTAuthentication()._decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                return Response({"detail": "Invalid token type"}, status=400)

            refresh_token = RefreshToken.objects.get(
                id=payload.get("id"), user_id=payload.get("user_id")
            )
        except RefreshToken.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=401)

        if not refresh_token.is_valid():
            return Response({"detail": "Refresh token expired"}, status=401)

        new_access = AccessToken.objects.create(
            user=refresh_token.user,
            expires_at=timezone.now() + datetime.timedelta(hours=1),
            device_id=refresh_token.device_id,
            user_agent=refresh_token.user_agent,
            ip_address=refresh_token.ip_address,
        )

        return Response(
            {"access_token": new_access.token},
            status=status.HTTP_200_OK,
        )


class DeviceListView(APIView):
    """Get a list of active devices"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        tokens = AccessToken.objects.filter(
            user=request.user, expires_at__gt=timezone.now()
        )
        serializer = AccessTokenSerializer(tokens, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeviceDeleteView(APIView):
    """Logout a specific device"""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, pk):
        try:
            token = AccessToken.objects.get(pk=pk, user=request.user)
            token.delete()
            return Response(
                {"detail": "Device logged out successfully"}, status=status.HTTP_200_OK
            )
        except AccessToken.DoesNotExist:
            return Response(
                {"detail": "Device not found"}, status=status.HTTP_404_NOT_FOUND
            )


class DeviceLogoutOthersView(APIView):
    """Log out all devices except the current one"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        current_device_id = request.data.get("device_id")
        if not current_device_id:
            return Response(
                {"detail": "device_id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        AccessToken.objects.filter(user=request.user).exclude(
            device_id=current_device_id
        ).delete()

        return Response(
            {"detail": "All other devices logged out"}, status=status.HTTP_200_OK
        )
