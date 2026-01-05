"""
# user/views.py

# pyright: ignore[reportMissingTypeStubs]
"""

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, views
from rest_framework.request import Request
from rest_framework.response import Response

from . import serializers
from .models import User, UserDevice, VerificationCode
from .utils import decode_jwt, generate_tokens, send_login_code


@extend_schema(tags=["User"])
class SessionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserSerializer

    def get(self, request):
        """Получить данные текущего пользователя."""
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


@extend_schema(tags=["User"])
class RequestCodeView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RequestCodeSerializer

    def post(self, request):
        """Запрос кода верификации (Email/Phone)."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        type = serializer.validated_data["type"]

        vc = VerificationCode.create_with_code(target=target, type=type)

        match type:
            case "email":
                send_login_code(email=target, code=vc.code)
                print(vc.code)
        return Response({"detail": "Code sent"})


@extend_schema(tags=["User"], responses={200: serializers.TokenResponseSerializer})
class EnterCodeView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.EnterCodeSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user, access, refresh = serializer.save()

        res = Response(
            {
                "access": access,
                "user": serializers.UserSerializer(
                    user, context={"request": request}
                ).data,
            }
        )

        res.set_cookie(
            "refresh",
            refresh,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            secure=settings.SESSION_COOKIE_SECURE,
            domain=settings.SESSION_COOKIE_DOMAIN,
        )

        return res


@extend_schema(tags=["User"], responses={200: serializers.RefreshResponseSerializer})
class RefreshView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RefreshTokenSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(
            data={"refresh_token": request.COOKIES.get("refresh")}
        )
        serializer.is_valid(raise_exception=True)
        user, access, refresh = serializer.save()

        res = Response(
            {
                "access": access,
                "user": serializers.UserSerializer(
                    user, context={"request": request}
                ).data,
            }
        )

        res.set_cookie(
            "refresh",
            refresh,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            secure=settings.SESSION_COOKIE_SECURE,
            domain=settings.SESSION_COOKIE_DOMAIN,
        )
        return res


@extend_schema(tags=["User"])
class DeviceListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserDeviceSerializer

    def get(self, request):
        """Список активных устройств пользователя."""
        devices = UserDevice.objects.filter(user=request.user, is_active=True)
        serializer = self.serializer_class(devices, many=True)
        return Response(serializer.data)


@extend_schema(tags=["User"])
class DeviceDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserDeviceSerializer

    def delete(self, request: Request, pk) -> Response:
        """Деактивация (разлогин) конкретного устройства."""
        device = get_object_or_404(UserDevice, pk=pk, user=request.user, is_active=True)
        device.is_active = False
        device.save(update_fields=["is_active"])
        return Response(
            {"detail": "Device deactivated"}, status=status.HTTP_204_NO_CONTENT
        )


# @extend_schema(tags=["User"])
# class DeviceLogoutOthersView(views.APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request: Request) -> Response:

#         current_device_id = (
#             request.auth.get("device_id") if isinstance(request.auth, dict) else None
#         )

#         qs = UserDevice.objects.filter(user=request.user)
#         if current_device_id:
#             qs = qs.exclude(device_id=current_device_id)

#         qs.update(is_active=False)
#         return Response({"detail": "Other sessions closed"})
