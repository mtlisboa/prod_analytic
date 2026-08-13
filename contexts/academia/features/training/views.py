from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import TrainingRecordForm, TrainingSetFormSet
from .models import TrainingRecord


@login_required
def create_training(request):
    if not request.user.exercises.exists():
        messages.info(request, "Cadastre seu primeiro exercício antes de registrar um treino.")
        return redirect("academia:exercise_create")

    record = TrainingRecord(user=request.user)
    form = TrainingRecordForm(request.POST or None, instance=record, user=request.user)
    now = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
    initial = [{"position": number, "performed_at": now, "rest_time_seconds": 60} for number in range(1, 4)]
    formset = TrainingSetFormSet(
        request.POST or None, instance=record, prefix="sets", form_kwargs={"user": request.user},
        initial=initial if request.method != "POST" else None,
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            formset.instance = record
            formset.save()
        messages.success(request, "Treino registrado com sucesso.")
        return redirect("academia:dashboard")
    return render(request, "academia/training_form.html", {"form": form, "formset": formset})
