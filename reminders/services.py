import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Reminder

logger = logging.getLogger(__name__)


def _matching_occurrence(birthday: date, days_before: int, today: date) -> date | None:
    """The birthday occurrence (this year's or next year's) that `today` is
    `days_before` days ahead of, if any."""
    for year in (today.year, today.year + 1):
        try:
            occurrence = birthday.replace(year=year)
        except ValueError:
            continue  # Feb 29 birthday, non-leap year
        if occurrence - timedelta(days=days_before) == today:
            return occurrence
    return None


def send_due_reminders() -> int:
    """Checks active reminders and emails owners whose notify window has arrived.

    Safe to call repeatedly (e.g. every few minutes from an external cron):
    each reminder only fires once per calendar year via last_notified_year.
    """
    now = timezone.localtime(timezone.now(), ZoneInfo(settings.TIME_ZONE))
    today = now.date()
    sent = 0

    reminders = Reminder.objects.filter(active=True).select_related(
        'contact', 'contact__owner', 'contact__owner__user'
    )

    for reminder in reminders:
        if reminder.last_notified_year == today.year:
            continue

        occurrence = _matching_occurrence(
            reminder.contact.birthday, reminder.days_before, today)
        if occurrence is None:
            continue

        if now.time() < reminder.notify_at:
            continue

        owner_email = reminder.contact.owner.user.email
        if not owner_email:
            logger.warning(
                "Skipping reminder %s: owner has no email", reminder.id)
            continue

        turning = occurrence.year - reminder.contact.birthday.year
        context = {
            'contact_name': reminder.contact.name,
            'birthday_date': occurrence.strftime('%d/%m/%Y'),
            'turning': turning,
            'relationship': reminder.contact.relationship,
            'days_before': reminder.days_before,
            'site_url': settings.SITE_URL,
        }

        subject = f"Aniversário de {reminder.contact.name} chegando!"
        text_body = render_to_string('emails/birthday_reminder.txt', context)
        html_body = render_to_string('emails/birthday_reminder.html', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[owner_email],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)

        reminder.last_notified_year = today.year
        reminder.save(update_fields=['last_notified_year'])
        sent += 1

    return sent
