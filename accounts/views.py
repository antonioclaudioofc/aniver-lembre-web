from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import (
    ProfileRegisterForm,
    LoginForm,
    VerifyEmailForm,
    PasswordResetRequestForm,
    SetNewPasswordForm,
    ProfileEditForm,
)
from .models import Profile
from .services import (
    send_verification_code,
    verify_code,
    can_resend_code,
    send_password_reset_code,
    verify_reset_code,
    can_resend_reset_code,
    clear_reset_code,
)
from .utils import get_profile


def _home_redirect(user):
    if user.is_superuser:
        return redirect('panel:overview')
    return redirect('/')


def index(request):
    if request.user.is_authenticated:
        return _home_redirect(request.user)
    return render(request, 'accounts/index.html')


def register(request):
    if request.method == "POST":
        form = ProfileRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_code(get_profile(user))
            request.session['pending_verification_user_id'] = user.id
            return redirect('accounts:verify_email')
    else:
        form = ProfileRegisterForm()
    return render(request, 'register/index.html', {"form": form})


def login(request):
    if request.user.is_authenticated:
        return _home_redirect(request.user)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            if not user.is_active:
                send_verification_code(get_profile(user))
                request.session['pending_verification_user_id'] = user.id
                return redirect('accounts:verify_email')
            auth_login(request, user)
            return _home_redirect(user)
    else:
        form = LoginForm()
    return render(request, 'login/index.html', {"form": form})


def verify_email(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        return redirect('accounts:login')

    profile = Profile.objects.select_related(
        'user').filter(user_id=user_id).first()
    if profile is None or profile.email_verified:
        del request.session['pending_verification_user_id']
        return redirect('accounts:login')

    resend_notice = None
    service_error = None
    form = VerifyEmailForm()

    if request.method == "POST":
        if request.POST.get('action') == 'resend':
            if can_resend_code(profile):
                send_verification_code(profile)
                resend_notice = 'Enviamos um novo código para o seu e-mail.'
            else:
                resend_notice = 'Aguarde um pouco antes de pedir outro código.'
        else:
            form = VerifyEmailForm(request.POST)
            if form.is_valid():
                ok, service_error = verify_code(
                    profile, form.cleaned_data['code'])
                if ok:
                    del request.session['pending_verification_user_id']
                    auth_login(request, profile.user)
                    return redirect(reverse('dashboard:index') + '?email_verified=1')

    return render(request, 'verify_email/index.html', {
        'form': form,
        'email': profile.user.email,
        'service_error': service_error,
        'resend_notice': resend_notice,
    })


def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            user = User.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            ).first()
            if user is not None and user.email:
                send_password_reset_code(get_profile(user))
                request.session['pending_reset_user_id'] = user.id
            return redirect('accounts:password_reset_confirm')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'password_reset/request.html', {"form": form})


def password_reset_confirm(request):
    if request.user.is_authenticated:
        return redirect('/')

    user_id = request.session.get('pending_reset_user_id')
    if not user_id:
        return redirect('accounts:password_reset_request')

    profile = Profile.objects.select_related(
        'user').filter(user_id=user_id).first()
    if profile is None:
        del request.session['pending_reset_user_id']
        return redirect('accounts:password_reset_request')

    resend_notice = None
    service_error = None
    form = VerifyEmailForm()

    if request.method == "POST":
        if request.POST.get('action') == 'resend':
            if can_resend_reset_code(profile):
                send_password_reset_code(profile)
                resend_notice = 'Enviamos um novo código para o seu e-mail.'
            else:
                resend_notice = 'Aguarde um pouco antes de pedir outro código.'
        else:
            form = VerifyEmailForm(request.POST)
            if form.is_valid():
                ok, service_error = verify_reset_code(
                    profile, form.cleaned_data['code'])
                if ok:
                    request.session['reset_code_verified_user_id'] = profile.user.id
                    return redirect('accounts:password_reset_new_password')

    return render(request, 'password_reset/confirm.html', {
        'form': form,
        'service_error': service_error,
        'resend_notice': resend_notice,
    })


def password_reset_new_password(request):
    if request.user.is_authenticated:
        return redirect('/')

    user_id = request.session.get('pending_reset_user_id')
    verified_user_id = request.session.get('reset_code_verified_user_id')
    if not user_id or user_id != verified_user_id:
        return redirect('accounts:password_reset_request')

    profile = Profile.objects.select_related(
        'user').filter(user_id=user_id).first()
    if profile is None:
        return redirect('accounts:password_reset_request')

    form = SetNewPasswordForm(user=profile.user)

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST, user=profile.user)
        if form.is_valid():
            profile.user.set_password(form.cleaned_data['new_password'])
            profile.user.save(update_fields=['password'])
            clear_reset_code(profile)
            del request.session['pending_reset_user_id']
            del request.session['reset_code_verified_user_id']
            return redirect(reverse('accounts:login') + '?password_reset=1')

    return render(request, 'password_reset/new_password.html', {
        'form': form,
    })


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('/accounts/login/')


@login_required
def profile(request):
    profile_obj = get_profile(request.user)

    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            email_changed = form.cleaned_data['email'] != request.user.email
            user = form.save()

            if email_changed:
                profile_obj.email_verified = False
                profile_obj.save(update_fields=['email_verified'])
                send_verification_code(profile_obj)
                request.session['pending_verification_user_id'] = user.id
                return redirect('accounts:verify_email')

            return redirect(reverse('accounts:profile') + '?profile_updated=1')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'profile/index.html', {
        'user': request.user,
        'form': form,
    })
