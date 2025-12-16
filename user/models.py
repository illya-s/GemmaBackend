# user/models.py

import hashlib
import secrets

import jwt
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from user.managers import UserManager


class Role(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return str(self.name)


class User(AbstractBaseUser, PermissionsMixin):
    """Main User model"""

    PROVIDERS = [
        ("local", "Local"),
        ("google", "Google"),
    ]

    uid = models.CharField(max_length=64, unique=True)

    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    provider = models.CharField(
        max_length=20,
        choices=PROVIDERS,
        default="local",
    )

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.uid:
            base_str = f"{self.pk}-{self.username or ''}-{self.email}"
            self.uid = hashlib.sha256(base_str.encode()).hexdigest()[:8]
            super().save(update_fields=["uid"])

    def __str__(self):
        return str(self.uid)


class VerificationCode(models.Model):
    """Model for temp login codes"""

    TYPE_CHOICES = (
        ("email", "Email"),
        ("phone", "Phone"),
    )

    target = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    code = models.CharField(max_length=6, editable=False)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updates_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["target", "type"]),
        ]

    def _generate_code(self) -> str:
        """Generates a 6-digit code."""
        return get_random_string(6, allowed_chars="0123456789")

    def save(self, *args, **kwargs):
        if self.pk:
            orig = VerificationCode.objects.get(pk=self.pk)
            for field in ("target", "type", "code"):
                if getattr(self, field) != getattr(orig, field):
                    raise ValueError(f"Field '{field}' is read-only")
        else:
            VerificationCode.objects.filter(
                target=self.target,
                type=self.type,
                is_used=False,
            ).update(is_used=True)

            self.code = self._generate_code()


        super().save(*args, **kwargs)

    def check_code(self, code: str) -> bool:
        if self.code != code:
            return False

        if self.is_used or self.is_expired():
            return False

        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])
        return True

    def is_expired(self) -> bool:
        """Determines whether the code has expired"""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return f"{self.target}"


class AccessToken(models.Model):
    """Access Token"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="access_tokens"
    )
    expires_at = models.DateTimeField()

    device_id = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        token = jwt.encode(
            {
                "id": self.pk,
                "user_id": self.user.pk,
                "device_id": self.device_id,
                "exp": int(self.expires_at.timestamp()),
                "type": "access",
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token

    def is_valid(self):
        """Determines whether the token has expired"""
        return self.expires_at > timezone.now()


class RefreshToken(models.Model):
    """Refresh Token"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    expires_at = models.DateTimeField()

    device_id = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        token = jwt.encode(
            {
                "id": self.pk,
                "user_id": self.user.pk,
                "device_id": self.device_id,
                "exp": int(self.expires_at.timestamp()),
                "type": "refresh",
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token

    def is_valid(self):
        """Determines whether the token has expired"""
        return self.expires_at > timezone.now()
