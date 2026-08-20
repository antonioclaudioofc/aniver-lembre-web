from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileRegisterForm, LoginForm, VerifyEmailForm
from .models import Profile
from .services import send_verification_code, verify_code, can_resend_code


def index(request):
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'accounts/index.html')


def register(request):
    if request.method == "POST":
        form = ProfileRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_code(user.profile)
            request.session['pending_verification_user_id'] = user.id
            return redirect('accounts:verify_email')
    else:
        form = ProfileRegisterForm()
    return render(request, 'register/index.html', {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            if not user.is_active:
                send_verification_code(user.profile)
                request.session['pending_verification_user_id'] = user.id
                return redirect('accounts:verify_email')
            auth_login(request, user)
            return redirect("/")
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
                    return redirect('/')

    return render(request, 'verify_email/index.html', {
        'form': form,
        'email': profile.user.email,
        'service_error': service_error,
        'resend_notice': resend_notice,
    })


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('/accounts/login/')


@login_required
def profile(request):
    return render(request, 'profile/index.html', {
        'user': request.user,
    })
