from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from contacts.models import Contact
from contacts.forms import ContactForm
from reminders.forms import ReminderForm
from reminders.models import Reminder

REMINDERS_PER_PAGE = 9
PAGINATION_WINDOW = 2

MONTH_LABELS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez',
}


def _days_until_birthday(birthday, today):
    for year in (today.year, today.year + 1):
        try:
            occurrence = birthday.replace(year=year)
        except ValueError:
            continue  # 29/fev em ano não bissexto
        if occurrence >= today:
            return (occurrence - today).days
    return None


def _filtered_reminders(request, profile):
    reminders = Reminder.objects.filter(contact__owner=profile).select_related(
        'contact').order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reminders = reminders.filter(contact__name__icontains=search_query)

    selected_month = request.GET.get('month')
    selected_month = int(selected_month) if selected_month and selected_month.isdigit() and 1 <= int(
        selected_month) <= 12 else None
    if selected_month:
        reminders = reminders.filter(
            contact__birthday__month=selected_month)

    return reminders, search_query, selected_month


def _month_options(profile, base_qd):
    counts = (
        Reminder.objects.filter(contact__owner=profile)
        .annotate(month=ExtractMonth('contact__birthday'))
        .values('month')
        .annotate(count=Count('id'))
    )
    counts_by_month = {row['month']: row['count'] for row in counts}

    months = []
    for number, label in MONTH_LABELS.items():
        qd = base_qd.copy()
        qd['month'] = number
        months.append({
            'number': number,
            'label': label,
            'count': counts_by_month.get(number, 0),
            'qs': qd.urlencode(),
        })
    return months


def _redirect_to_index(page=None, status=None):
    url = reverse('dashboard:index')
    params = []
    if page:
        params.append(f'page={page}')
    if status:
        params.append(f'{status}=1')
    if params:
        url += '?' + '&'.join(params)
    return redirect(url)


def _pagination_range(current, total, window=PAGINATION_WINDOW):
    """Lista de páginas a exibir, com None marcando reticências.
    Ex.: current=6, total=20 -> [1, None, 4, 5, 6, 7, 8, None, 20]."""
    if total <= 1:
        return []

    pages = {1, total}
    for p in range(current - window, current + window + 1):
        if 1 <= p <= total:
            pages.add(p)

    result = []
    prev = None
    for p in sorted(pages):
        if prev is not None and p - prev > 1:
            result.append(None)
        result.append(p)
        prev = p
    return result


def _dashboard_context(request, profile):
    reminders, search_query, selected_month = _filtered_reminders(
        request, profile)
    paginator = Paginator(reminders, REMINDERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    today = timezone.localdate()
    for r in page_obj:
        r.days_until_birthday = _days_until_birthday(
            r.contact.birthday, today)

    base_qd = request.GET.copy()
    base_qd.pop('page', None)

    all_qd = base_qd.copy()
    all_qd.pop('month', None)

    page_qd = base_qd.copy()
    page_qs = ('&' + page_qd.urlencode()) if page_qd else ''

    return {
        'page_obj': page_obj,
        'reminders': page_obj,
        'search_query': search_query,
        'selected_month': selected_month,
        'months': _month_options(profile, base_qd),
        'all_months_qs': all_qd.urlencode(),
        'page_qs': page_qs,
        'pagination_range': _pagination_range(page_obj.number, paginator.num_pages),
    }


@login_required
def index(request):
    profile = request.user.profile

    context = _dashboard_context(request, profile)
    context['contacts'] = Contact.objects.filter(owner=profile)
    context['contact_form'] = ContactForm()
    context['reminder_form'] = ReminderForm()

    return render(request, 'dashboard/index.html', context)


@login_required
def create_reminder(request):
    if request.method != 'POST':
        return redirect(reverse('dashboard:index'))

    profile = request.user.profile
    reminder_id = request.POST.get('reminder_id')

    reminder_instance = None
    contact_instance = None

    if reminder_id:
        reminder_instance = get_object_or_404(
            Reminder, pk=reminder_id, contact__owner=profile)
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
        status = 'reminder_updated' if reminder_id else 'reminder_created'
        return _redirect_to_index(request.POST.get('page'), status)

    context = _dashboard_context(request, profile)
    context['contacts'] = Contact.objects.filter(owner=profile)
    context['contact_form'] = contact_form
    context['reminder_form'] = reminder_form
    context['show_dialog'] = True
    context['is_editing'] = bool(reminder_id)
    context['current_reminder_id'] = reminder_id or ''

    return render(request, 'dashboard/index.html', context)


@login_required
def delete_reminder(request, reminder_id):
    profile = request.user.profile
    if request.method == 'POST':
        reminder = get_object_or_404(
            Reminder, pk=reminder_id, contact__owner=profile)
        reminder.delete()
        return _redirect_to_index(request.POST.get('page'), 'reminder_deleted')
    return _redirect_to_index(request.POST.get('page'))
