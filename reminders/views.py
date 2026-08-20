import hmac

from django.conf import settings
from django.http import JsonResponse

from .services import send_due_reminders


def run_due_reminders(request):
    token = request.GET.get('token', '')
    expected = settings.CRON_SECRET
    if not expected or not hmac.compare_digest(token, expected):
        return JsonResponse({'detail': 'Forbidden'}, status=403)

    sent = send_due_reminders()
    return JsonResponse({'sent': sent})
