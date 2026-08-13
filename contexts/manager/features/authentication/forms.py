from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {"username": "Usuário"}


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuário")
    password = forms.CharField(label="Senha", strip=False, widget=forms.PasswordInput)
