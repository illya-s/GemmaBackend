# user/rate_limit.py
from django.utils import timezone
from django.http import JsonResponse
from .models import VerificationCode


class VerificationCodeRateLimitMixin:
    RATE_LIMIT = 4
    RATE_PERIOD = 60

    def check_rate_limit(self, target: str, type_: str):
        since = timezone.now() - timezone.timedelta(seconds=self.RATE_PERIOD)

        count = VerificationCode.objects.filter(
            target=target,
            type=type_,
            created_at__gte=since,
        ).count()

        if count >= self.RATE_LIMIT:
            return False

        return True
