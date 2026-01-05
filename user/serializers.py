"""user/serializers.py"""

import jwt
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

from user.utils import generate_tokens, get_ip_from_request

from .models import RefreshToken, User, UserDevice, VerificationCode


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_avatar(self, obj: User) -> str | None:
        request = self.context.get("request")
        if request is None:
            return obj.avatar.url if obj.avatar else None
        return request.build_absolute_uri(obj.avatar.url) if obj.avatar else None

    def get_role(self, obj: User) -> str | None:
        return obj.role.name if obj.role else None

    class Meta:
        model = User
        fields = [
            "uid",
            "username",
            "email",
            "phone",
            "avatar",
            "role",
            "is_guest",
            "date_joined",
        ]


class RequestCodeSerializer(serializers.Serializer):
    target = serializers.CharField(help_text="Email address or Phone number")
    type = serializers.ChoiceField(choices=[("email", "Email"), ("phone", "Phone")])


class EnterCodeSerializer(serializers.Serializer):
    target = serializers.CharField()
    type = serializers.ChoiceField(choices=[("email", "Email"), ("phone", "Phone")])
    code = serializers.CharField(max_length=6)
    device_id = serializers.CharField(max_length=255)
    device_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    def validate(self, data):
        target = data.get("target")
        type = data.get("type")
        code = data.get("code")

        if not target:
            raise serializers.ValidationError("L'indirizzo email è obbligatorio.")

        if not type:
            raise serializers.ValidationError("Il tipo di operazione è obbligatorio.")

        if not code:
            raise serializers.ValidationError("Il codice di verifica è obbligatorio.")

        record = (
            VerificationCode.objects.filter(target=target, type=type, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not record:
            raise serializers.ValidationError("Codice non trovato o già utilizzato.")

        if not record.check_code(code):
            raise serializers.ValidationError("Codice errato.")

        return data

    @transaction.atomic
    def create(self, validated_data):  # pyright: ignore[reportIncompatibleMethodOverride]
        request = self.context.get("request")

        target = validated_data["target"]
        type = validated_data["type"]
        device_id = validated_data["device_id"]
        device_name = validated_data["device_name"]

        user, created = User.objects.get_or_create(
            **{type: target}, defaults={"username": f"user_{target}"}
        )
        device, _ = UserDevice.objects.get_or_create(
            user=user,
            device_id=device_id,
            name=device_name,
            user_agent=request.headers.get("User-Agent"),
            ip_address=get_ip_from_request(request),
        )

        access, refresh, jti = generate_tokens(user, device.pk)

        RefreshToken.objects.filter(user=user, device=device, is_revoked=False).exclude(
            jti=jti
        ).update(is_revoked=True, last_used_at=timezone.now())

        return user, access, refresh

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update operation is not supported!")


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, data):
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            raise NotAuthenticated("Refresh token required")

        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise NotAuthenticated("Refresh token expired")
        except jwt.InvalidTokenError:
            raise NotAuthenticated("Invalid token")

        if payload.get("type") != "refresh":
            raise NotAuthenticated("Invalid token type")

        db_token = (
            RefreshToken.objects.filter(
                jti=payload.get("jti"), is_revoked=False, expires_at__gt=timezone.now()
            )
            .select_related("user", "device")
            .first()
        )

        if not db_token:
            raise NotAuthenticated("Token is invalid or revoked")

        data["refresh_token"] = db_token
        return data

    @transaction.atomic
    def create(self, validated_data):
        db_token = validated_data["refresh_token"]

        new_access, new_refresh, _ = generate_tokens(
            user=db_token.user, device_id=db_token.device.pk
        )

        db_token.last_used_at = timezone.now()
        db_token.is_revoked = True
        db_token.save()

        return db_token.user, new_access, new_refresh

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update operation is not supported!")


class RefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class DeviceRefreshTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshToken
        fields = ("id", "expires_at", "created_at", "is_revoked")


class UserDeviceSerializer(serializers.ModelSerializer):
    refresh_tokens = serializers.SerializerMethodField()

    @extend_schema_field(DeviceRefreshTokenSerializer(many=True))
    def get_refresh_tokens(self, obj):
        return DeviceRefreshTokenSerializer(
            obj.device_refresh_token.order_by("is_revoked"), many=True
        ).data

    class Meta:
        model = UserDevice
        fields = "__all__"
