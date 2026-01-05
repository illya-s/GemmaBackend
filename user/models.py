# user/models.py

import hashlib
import uuid

import jwt
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from user.managers import UserManager


class Role(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return str(self.name)


def get_default_role():
    from user.models import Role

    return Role.objects.get(name="user").id


class User(AbstractBaseUser, PermissionsMixin):
    """Main User model"""

    PROVIDERS = [
        ("local", "Local"),
        ("google", "Google"),
    ]

    uid = models.CharField(max_length=32, unique=True)

    username = models.CharField(max_length=255, unique=True)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    provider = models.CharField(max_length=20, choices=PROVIDERS, default="local")

    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, default=get_default_role, null=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def clean(self):
        if not self.is_guest and not (self.email or self.phone):
            raise ValidationError("Guest user cannot have email or phone")

    def generate_hash(self):
        return uuid.uuid4().hex

    def save(self, *args, **kwargs):
        if not self.pk:
            self.set_unusable_password()

        if not self.uid:
            self.uid = self.generate_hash()

        if self.is_guest and not self.username:
            self.username = f"guest_{self.uid}"

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.username)


class UserDevice(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    device_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True)

    user_agent = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    last_ip_changed_at = models.DateTimeField(null=True, blank=True)

    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "device_id"],
                name="unique_user_device",
            )
        ]

        indexes = [
            models.Index(fields=["user", "device_id"]),
        ]

    def update_device_ip(self, current_ip: str) -> bool:
        if self.ip_address != current_ip:
            self.ip_address = current_ip
            self.last_ip_changed_at = timezone.now()
            self.save(update_fields=["ip_address", "last_ip_changed_at"])
            return True
        else:
            return False

    def __str__(self):
        return f"{self.user} - {self.device_id}"


class RefreshToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(
        UserDevice, on_delete=models.CASCADE, related_name="device_refresh_token"
    )

    jti = models.UUIDField(unique=True)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    is_revoked = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "device"]),
            models.Index(fields=["jti"]),
        ]


class VerificationCode(models.Model):
    """Model for temp login codes"""

    TYPE_CHOICES = (
        ("email", "Email"),
        ("phone", "Phone"),
    )

    target = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    _code_hash = models.CharField(max_length=128, null=True, db_column="code")

    # attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    __plain_code = None

    class Meta:
        indexes = [
            models.Index(fields=["target", "type"]),
        ]

    @classmethod
    def _generate_code(cls) -> str:
        """Generates a 6-digit code."""
        return get_random_string(6, allowed_chars="0123456789")

    @classmethod
    def _hash_code(cls, code: str) -> str:
        """Возвращает SHA256-хэш кода."""
        return hashlib.sha256(code.encode()).hexdigest()

    @property
    def code(self):
        """Возвращает исходный код только если он был сгенерирован при создании."""
        if self.__plain_code is None:
            raise AttributeError(
                "Код недоступен. Он не хранится в базе по соображениям безопасности."
            )
        return self.__plain_code

    @code.setter
    def code(self, value):
        """Запрещаем изменение кода напрямую."""
        raise AttributeError("Нельзя изменять код вручную.")

    def check_code(self, code: str) -> bool:
        if self.is_used or self.is_expired():
            return False

        if self._code_hash != self._hash_code(code):
            return False

        # if self.attempts >= 5:
        #     return False

        self.is_used = True
        self.save(update_fields=["is_used"])
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            orig = VerificationCode.objects.get(pk=self.pk)
            for field in ("target", "type", "_code_hash"):
                if getattr(self, field) != getattr(orig, field):
                    raise ValueError(f"Field '{field}' is read-only")
        else:
            VerificationCode.objects.filter(
                target=self.target,
                type=self.type,
                is_used=False,
            ).update(is_used=True)

        super().save(*args, **kwargs)

    @classmethod
    def create_with_code(cls, type: str, target: str):
        """Создает новый VerificationCode и возвращает экземпляр с доступом к plain_code."""
        code = cls._generate_code()
        obj = cls.objects.create(
            type=type, target=target, _code_hash=cls._hash_code(code)
        )
        obj.__plain_code = code
        return obj

    def is_expired(self) -> bool:
        """Determines whether the code has expired"""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return f"{self.target}"
