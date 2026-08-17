from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("manager:home")
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "manager:home")
    return render(request, "manager/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("manager:home")
    if User.objects.exists():
        messages.info(request, "O cadastro já foi concluído. Entre com sua conta.")
        return redirect("manager:login")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Conta criada. Bom treino!")
        return redirect("manager:home")
    return render(request, "manager/signup.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("manager:login")
    return redirect("manager:home")
