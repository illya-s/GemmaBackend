from django.contrib.auth.base_user import BaseUserManager
from django.utils.crypto import get_random_string


class UserManager(BaseUserManager):
    """Main User Manager"""

    def create_user(self, email, username=None, avatar=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            avatar=avatar,
            **extra_fields,
        )
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, avatar=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, username=username, avatar=avatar, **extra_fields)