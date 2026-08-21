from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, error_messages={
        "unique": "Este usuário já possui um perfil associado.",
        "null": "Usuário obrigatório"
    })

    updated_at = models.DateTimeField(auto_now=True)

    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verification_attempts = models.PositiveSmallIntegerField(default=0)

    reset_code = models.CharField(max_length=6, blank=True)
    reset_sent_at = models.DateTimeField(null=True, blank=True)
    reset_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
