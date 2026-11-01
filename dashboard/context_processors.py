from reminders.models import Reminder


def nav(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    count = Reminder.objects.filter(contact__owner__user=user).count()
    return {"nav_people_count": count}
