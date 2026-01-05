import datetime
import uuid
from typing import Union

import jwt
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.request import Request

from user.models import RefreshToken, User


def send_login_code(email, code):
    msg = EmailMultiAlternatives(
        "Ваш код для входа",
        f"Ваш код: {code}\n\nЕсли вы не запрашивали вход, просто проигнорируйте это письмо.",
        settings.EMAIL,
        [email],
    )
    msg.attach_alternative(
        render_to_string("authCode.html", {"code": code}), "text/html"
    )
    msg.send()


def get_ip_from_request(request: Request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def get_refresh_token(
    user_id: int,
    device_id: int,
    jti: str,
    exp: Union[int, datetime.datetime],
) -> str:
    return jwt.encode(
        {
            "user_id": user_id,
            "device_id": device_id,
            "jti": jti,
            "exp": exp,
            "type": "refresh",
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def generate_tokens(user: User, device_id: int):
    """Генерирует пару Access и Refresh токенов."""
    jti = str(uuid.uuid4())
    access_exp = timezone.now() + datetime.timedelta(minutes=60)
    refresh_exp = timezone.now() + datetime.timedelta(days=30)

    access_token = jwt.encode(
        {
            "user_id": user.pk,
            "device_id": device_id,
            "exp": access_exp,
            "type": "access",
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    refresh_token = get_refresh_token(
        user_id=user.pk, device_id=device_id, jti=jti, exp=refresh_exp
    )

    RefreshToken.objects.create(
        user=user, device_id=device_id, jti=jti, expires_at=refresh_exp
    )

    return access_token, refresh_token, jti


def decode_jwt(token: str):
    """Декодирует JWT с обработкой ошибок."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
