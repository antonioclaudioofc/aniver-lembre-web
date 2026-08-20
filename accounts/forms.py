from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Profile


class ProfileRegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label="Confirme sua senha",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["first_name", "username", "email"]
        labels = {
            "first_name": "Nome",
            "username": "Usuário",
            "email": "E-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("As senhas devem ser iguais.")

        return confirm_password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("E-mail já cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Kept inactive until the e-mail verification code is confirmed.
        user.is_active = False

        if commit:
            user.save()

            Profile.objects.create(
                user=user,
                updated_at=None
            )

        return user


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Usuário ou e-mail")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")

        if identifier and password:
            user = User.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            ).first()

            if user is None or not user.check_password(password):
                raise ValidationError("Usuário ou senha inválidos.")

            cleaned_data["user"] = user

        return cleaned_data


class VerifyEmailForm(forms.Form):
    code = forms.CharField(
        label="Código de verificação",
        max_length=6,
        min_length=6,
    )

    def clean_code(self):
        code = self.cleaned_data.get("code", "")
        if not code.isdigit():
            raise ValidationError("O código deve conter apenas números.")
        return code
