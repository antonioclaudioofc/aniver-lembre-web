from django.core.management.base import BaseCommand

from reminders.services import send_due_reminders


class Command(BaseCommand):
    help = "Checks active reminders and emails owners whose notify window has arrived."

    def handle(self, *args, **options):
        sent = send_due_reminders()
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} reminder(s)."))
