from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.utils import get_profile
from contacts.forms import ContactForm
from contacts.models import Contact
from core.pagination import pagination_range
from reminders.forms import ReminderForm
from reminders.models import Reminder

from . import services

PEOPLE_PER_PAGE = 15
PAGINATION_WINDOW = 2
UPCOMING_LIMIT = 6

MONTH_CHOICES = [
    (1, "Janeiro"),
    (2, "Fevereiro"),
    (3, "Março"),
    (4, "Abril"),
    (5, "Maio"),
    (6, "Junho"),
    (7, "Julho"),
    (8, "Agosto"),
    (9, "Setembro"),
    (10, "Outubro"),
    (11, "Novembro"),
    (12, "Dezembro"),
]

NEXT_TARGETS = {"people": "dashboard:people"}


def _parse_month(raw):
    if raw and raw.isdigit() and 1 <= int(raw) <= 12:
        return int(raw)
    return None


def _user_reminders(profile):
    return Reminder.objects.filter(contact__owner=profile).select_related("contact")


def _search(reminders, request):
    query = request.GET.get("q", "").strip()
    if query:
        reminders = reminders.filter(contact__name__icontains=query)
    return reminders, query


def _redirect_target(next_key):
    return reverse(NEXT_TARGETS.get(next_key, "dashboard:index"))


def _redirect_back(next_key=None, page=None, status=None, saved=None):
    url = _redirect_target(next_key)
    params = []
    if page:
        params.append(f"page={page}")
    if status:
        params.append(f"{status}=1")
    if saved:
        params.append(f"saved={saved}")
    if params:
        url += "?" + "&".join(params)
    return redirect(url)


def _home_context(request, profile):
    today = timezone.localdate()
    everyone = services.annotate_all(_user_reminders(profile), today)
    calendar_payload = services.calendar_data(everyone, today)

    visible, query = _search(_user_reminders(profile), request)
    people = services.sort_by_proximity(services.annotate_all(visible, today))

    active_sorted = services.sort_by_proximity([r for r in everyone if r.active])
    featured = next((r for r in active_sorted if r.next_date), None)
    upcoming = [r for r in active_sorted if r is not featured][:UPCOMING_LIMIT]

    return {
        "today": today,
        "weekday": services.WEEKDAYS[today.weekday()],
        "total_people": len(everyone),
        "featured": featured,
        "upcoming": upcoming,
        "people": people,
        "search_query": query,
        "calendar_payload": calendar_payload,
        "modal_next": "",
    }


def _people_context(request, profile):
    today = timezone.localdate()
    reminders = _user_reminders(profile)
    reminders, query = _search(reminders, request)

    selected_month = _parse_month(request.GET.get("month"))
    if selected_month:
        reminders = reminders.filter(contact__birthday__month=selected_month)

    people = services.sort_by_proximity(services.annotate_all(reminders, today))
    paginator = Paginator(people, PEOPLE_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    page_qd = request.GET.copy()
    page_qd.pop("page", None)
    page_qs = ("&" + page_qd.urlencode()) if page_qd else ""

    counts = (
        _user_reminders(profile)
        .annotate(month=ExtractMonth("contact__birthday"))
        .values("month")
        .annotate(count=Count("id"))
    )
    counts_by_month = {row["month"]: row["count"] for row in counts}
    month_options = [
        {"number": n, "label": label, "count": counts_by_month.get(n, 0)}
        for n, label in MONTH_CHOICES
    ]

    base = _user_reminders(profile)
    return {
        "today": today,
        "page_obj": page_obj,
        "reminders": page_obj,
        "search_query": query,
        "selected_month": selected_month,
        "month_options": month_options,
        "page_qs": page_qs,
        "pagination_range": pagination_range(
            page_obj.number, paginator.num_pages, PAGINATION_WINDOW
        ),
        "total_people": base.count(),
        "active_count": base.filter(active=True).count(),
        "result_count": paginator.count,
        "modal_next": "people",
    }


def _with_forms(context, profile, contact_form=None, reminder_form=None):
    context["contacts"] = Contact.objects.filter(owner=profile)
    context["contact_form"] = contact_form or ContactForm()
    context["reminder_form"] = reminder_form or ReminderForm()
    return context


@login_required
def index(request):
    profile = get_profile(request.user)
    context = _with_forms(_home_context(request, profile), profile)
    return render(request, "dashboard/index.html", context)


@login_required
def people(request):
    profile = get_profile(request.user)
    context = _with_forms(_people_context(request, profile), profile)
    return render(request, "dashboard/people.html", context)


@login_required
def create_reminder(request):
    if request.method != "POST":
        return redirect(reverse("dashboard:index"))

    profile = get_profile(request.user)
    reminder_id = request.POST.get("reminder_id")
    next_key = request.POST.get("next")

    reminder_instance = None
    contact_instance = None

    if reminder_id:
        reminder_instance = get_object_or_404(
            Reminder, pk=reminder_id, contact__owner=profile
        )
        contact_instance = reminder_instance.contact

    contact_form = ContactForm(request.POST, instance=contact_instance)
    reminder_form = ReminderForm(request.POST, instance=reminder_instance)

    if contact_form.is_valid() and reminder_form.is_valid():
        contact = contact_form.save(commit=False)
        contact.owner = profile
        contact.save()

        reminder = reminder_form.save(commit=False)
        reminder.contact = contact
        reminder.save()
        status = "reminder_updated" if reminder_id else "reminder_created"
        return _redirect_back(
            next_key, request.POST.get("page"), status, saved=reminder.id
        )

    if next_key == "people":
        context = _people_context(request, profile)
        template = "dashboard/people.html"
    else:
        context = _home_context(request, profile)
        template = "dashboard/index.html"

    context = _with_forms(context, profile, contact_form, reminder_form)
    context["show_dialog"] = True
    context["is_editing"] = bool(reminder_id)
    context["current_reminder_id"] = reminder_id or ""

    return render(request, template, context)


@login_required
def delete_reminder(request, reminder_id):
    profile = get_profile(request.user)
    next_key = request.POST.get("next")
    if request.method == "POST":
        reminder = get_object_or_404(Reminder, pk=reminder_id, contact__owner=profile)
        reminder.delete()
        return _redirect_back(next_key, request.POST.get("page"), "reminder_deleted")
    return _redirect_back(next_key, request.POST.get("page"))
