import csv
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from contacts.models import Contact
from core.pagination import pagination_range
from reminders.models import Reminder
from .decorators import superuser_required

USERS_PER_PAGE = 12
REMINDERS_PER_PAGE = 12
PAGINATION_WINDOW = 2


def _redirect_with_status(url_name, page=None, status=None):
    url = reverse(url_name)
    params = []
    if page:
        params.append(f'page={page}')
    if status:
        params.append(f'{status}=1')
    if params:
        url += '?' + '&'.join(params)
    return redirect(url)


@superuser_required
def overview(request):
    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = Profile.objects.filter(email_verified=True).count()

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'verified_users': verified_users,
        'unverified_users': total_users - verified_users,
        'total_contacts': Contact.objects.count(),
        'total_reminders': Reminder.objects.count(),
        'active_reminders': Reminder.objects.filter(active=True).count(),
        'sent_this_year': Reminder.objects.filter(last_notified_year=today.year).count(),
        'active_tab': 'overview',
    }
    return render(request, 'panel/overview.html', context)


def _filtered_users(request):
    qs = User.objects.select_related('profile').order_by('-date_joined')
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
        )
    return qs, search_query


def _filtered_reminders(request):
    qs = Reminder.objects.select_related(
        'contact', 'contact__owner__user').order_by('-created_at')
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(contact__name__icontains=search_query)
            | Q(contact__owner__user__username__icontains=search_query)
            | Q(contact__owner__user__email__icontains=search_query)
        )
    return qs, search_query


@superuser_required
def users_list(request):
    qs, search_query = _filtered_users(request)

    paginator = Paginator(qs, USERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    base_qd = request.GET.copy()
    base_qd.pop('page', None)
    page_qs = ('&' + base_qd.urlencode()) if base_qd else ''

    return render(request, 'panel/users.html', {
        'page_obj': page_obj,
        'users': page_obj,
        'search_query': search_query,
        'page_qs': page_qs,
        'pagination_range': pagination_range(page_obj.number, paginator.num_pages, PAGINATION_WINDOW),
        'active_tab': 'users',
    })


@superuser_required
def toggle_user_active(request, user_id):
    if request.method != 'POST':
        return redirect('panel:users')

    target = get_object_or_404(User, pk=user_id)
    page = request.POST.get('page')

    if target.pk == request.user.pk:
        return _redirect_with_status('panel:users', page, 'cannot_change_self')

    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    status = 'user_activated' if target.is_active else 'user_deactivated'
    return _redirect_with_status('panel:users', page, status)


@superuser_required
def delete_user(request, user_id):
    if request.method != 'POST':
        return redirect('panel:users')

    target = get_object_or_404(User, pk=user_id)
    page = request.POST.get('page')

    if target.pk == request.user.pk or target.is_superuser:
        return _redirect_with_status('panel:users', page, 'cannot_change_self')

    target.delete()
    return _redirect_with_status('panel:users', page, 'user_deleted')


@superuser_required
def reminders_list(request):
    qs, search_query = _filtered_reminders(request)

    paginator = Paginator(qs, REMINDERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    base_qd = request.GET.copy()
    base_qd.pop('page', None)
    page_qs = ('&' + base_qd.urlencode()) if base_qd else ''

    return render(request, 'panel/reminders.html', {
        'page_obj': page_obj,
        'reminders': page_obj,
        'search_query': search_query,
        'page_qs': page_qs,
        'pagination_range': pagination_range(page_obj.number, paginator.num_pages, PAGINATION_WINDOW),
        'active_tab': 'reminders',
    })


@superuser_required
def export_users(request):
    qs, _ = _filtered_users(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'

    writer = csv.writer(response)
    writer.writerow(['Usuário', 'Nome', 'E-mail', 'E-mail verificado',
                     'Status', 'Admin', 'Cadastro'])
    for u in qs:
        writer.writerow([
            u.username,
            u.first_name,
            u.email,
            'Sim' if u.profile.email_verified else 'Não',
            'Ativo' if u.is_active else 'Inativo',
            'Sim' if u.is_superuser else 'Não',
            u.date_joined.strftime('%d/%m/%Y'),
        ])
    return response


@superuser_required
def export_reminders(request):
    qs, _ = _filtered_reminders(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lembretes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Contato', 'Dono (usuário)', 'Dono (e-mail)', 'Aniversário',
                     'Notificar às', 'Dias antes', 'Ativo', 'Último ano notificado'])
    for r in qs:
        writer.writerow([
            r.contact.name,
            r.contact.owner.user.username,
            r.contact.owner.user.email,
            r.contact.birthday.strftime('%d/%m/%Y'),
            r.notify_at.strftime('%H:%M'),
            r.days_before,
            'Sim' if r.active else 'Não',
            r.last_notified_year or '',
        ])
    return response
