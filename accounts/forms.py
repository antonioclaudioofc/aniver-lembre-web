from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q


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
        user.is_active = False

        if commit:
            user.save()

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


class PasswordResetRequestForm(forms.Form):
    identifier = forms.CharField(label="Usuário ou e-mail")


class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="Nova senha", widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(
        label="Confirme a nova senha", widget=forms.PasswordInput
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        validate_password(password, user=self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_new_password")

        if password and confirm and password != confirm:
            self.add_error("confirm_new_password",
                           "As senhas devem ser iguais.")

        if password and self.user and self.user.check_password(password):
            self.add_error(
                "new_password", "A nova senha deve ser diferente da senha atual.")

        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "email"]
        labels = {
            "first_name": "Nome",
            "email": "E-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("E-mail já cadastrado.")
        return email
