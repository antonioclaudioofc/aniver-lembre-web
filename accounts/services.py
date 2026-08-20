import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone

CODE_LENGTH = 6
CODE_TTL_MINUTES = 15
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS = 5


def _logo_url() -> str:
    return settings.SITE_URL.rstrip('/') + '/' + static('images/logo-email.png').lstrip('/')


def can_resend_code(profile) -> bool:
    if not profile.verification_sent_at:
        return True
    elapsed = (timezone.now() - profile.verification_sent_at).total_seconds()
    return elapsed >= RESEND_COOLDOWN_SECONDS


def send_verification_code(profile) -> None:
    code = f"{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}"
    profile.verification_code = code
    profile.verification_sent_at = timezone.now()
    profile.verification_attempts = 0
    profile.save(update_fields=[
        'verification_code', 'verification_sent_at', 'verification_attempts',
    ])

    context = {
        'first_name': profile.user.first_name,
        'code': code,
        'ttl_minutes': CODE_TTL_MINUTES,
        'logo_url': _logo_url(),
    }
    text_body = render_to_string('emails/verification_code.txt', context)
    html_body = render_to_string('emails/verification_code.html', context)

    email = EmailMultiAlternatives(
        subject="Confirme seu e-mail — AniverLembre",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[profile.user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)


def verify_code(profile, submitted_code: str) -> tuple[bool, str]:
    if profile.email_verified:
        return True, ''

    if not profile.verification_code or not profile.verification_sent_at:
        return False, 'Nenhum código pendente. Solicite um novo.'

    if profile.verification_attempts >= MAX_ATTEMPTS:
        return False, 'Muitas tentativas erradas. Solicite um novo código.'

    expires_at = profile.verification_sent_at + \
        timedelta(minutes=CODE_TTL_MINUTES)
    if timezone.now() > expires_at:
        return False, 'Esse código expirou. Solicite um novo.'

    if submitted_code != profile.verification_code:
        profile.verification_attempts += 1
        profile.save(update_fields=['verification_attempts'])
        return False, 'Código incorreto.'

    profile.email_verified = True
    profile.verification_code = ''
    profile.user.is_active = True
    profile.user.save(update_fields=['is_active'])
    profile.save(update_fields=['email_verified', 'verification_code'])
    return True, ''
