"""
# user/serializers.py
"""

import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import User, AccessToken, RefreshToken, LoginCode


class RequestCodeSerializer(serializers.Serializer):
    """Serializers registration requests and creates a new user"""

    email = serializers.CharField(max_length=255, required=True)

    def create(self, validated_data):
        email = validated_data["email"]
        now = timezone.now()

        recent_count = LoginCode.objects.filter(
            email=email, created_at__gte=now - datetime.timedelta(minutes=1)
        ).count()

        if recent_count >= 10:
            raise serializers.ValidationError("Too many requests. Try again later.")

        login_code = LoginCode.create_with_code(email=email)
        return {"email": email, "code": login_code.code}

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update operation is not supported!")


class EnterCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, required=True)
    code = serializers.CharField(max_length=6, required=True)
    device_id = serializers.CharField(max_length=255, required=True)

    def validate(self, data):
        email = data.get("email", None)
        code = data.get("code", None)

        if not email or not code:
            raise serializers.ValidationError("Требуется адрес электронной почты и код")

        record = (
            LoginCode.objects.filter(email=email, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not record:
            raise serializers.ValidationError("Код не найден или уже использован")

        if record.is_expired():
            raise serializers.ValidationError("Срок действия кода истёк")

        if not record.check_code(code):
            raise serializers.ValidationError("Неверный код.")

        record.is_used = True
        record.save(update_fields=["is_used"])

        return data

    def create(self, validated_data):
        email = validated_data["email"]
        device_id = validated_data["device_id"]

        user, created = User.objects.get_or_create(
            email=email, defaults={"username": email.split("@")[0], "is_active": True}
        )

        AccessToken.objects.filter(user=user, device_id=device_id).delete()
        RefreshToken.objects.filter(user=user, device_id=device_id).delete()

        now = timezone.now()
        access_token = AccessToken.objects.create(
            user=user,
            device_id=device_id,
            expires_at=now + datetime.timedelta(hours=1),
            user_agent=self.context["request"].META.get("HTTP_USER_AGENT"),
            ip_address=self.context["request"].META.get("REMOTE_ADDR"),
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            device_id=device_id,
            expires_at=now + datetime.timedelta(days=60),
            user_agent=self.context["request"].META.get("HTTP_USER_AGENT"),
            ip_address=self.context["request"].META.get("REMOTE_ADDR"),
        )

        return {
            "user": user,
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
        }

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update operation is not supported!")


class AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = [
            "id",
            "device_id",
            "user_agent",
            "ip_address",
            "expires_at",
            "created_at",
        ]
