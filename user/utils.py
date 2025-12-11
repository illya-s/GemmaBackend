from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


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
