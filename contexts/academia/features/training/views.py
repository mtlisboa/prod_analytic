from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    TrainingRecordForm,
    TrainingSetCreateFormSet,
    TrainingSetUpdateFormSet,
)
from .models import TrainingRecord


@login_required
def search_exercises(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    exercises = request.user.exercises.filter(
        active=True, name__icontains=query[:100]
    ).values("id", "name", "muscle_group").order_by("name")[:20]
    return JsonResponse({"results": list(exercises)})


@login_required
def create_training(request):
    if not request.user.exercises.exists():
        messages.info(request, "Cadastre seu primeiro exercício antes de registrar um treino.")
        return redirect("academia:exercise_create")

    record = TrainingRecord(user=request.user)
    form = TrainingRecordForm(request.POST or None, instance=record, user=request.user)
    now = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
    initial = [{"position": number, "performed_at": now, "rest_time_seconds": 60} for number in range(1, 4)]
    formset = TrainingSetCreateFormSet(
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
    return render(request, "academia/training_form.html", {"form": form, "formset": formset, "editing": False})


@login_required
def update_training(request, pk):
    record = get_object_or_404(TrainingRecord, pk=pk, user=request.user)
    form = TrainingRecordForm(request.POST or None, instance=record, user=request.user)
    formset = TrainingSetUpdateFormSet(
        request.POST or None, instance=record, prefix="sets",
        form_kwargs={"user": request.user},
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, "Treino atualizado com sucesso.")
        return redirect("academia:dashboard")
    return render(request, "academia/training_form.html", {
        "form": form, "formset": formset, "editing": True, "record": record,
    })


@login_required
def delete_training(request, pk):
    record = get_object_or_404(TrainingRecord, pk=pk, user=request.user)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Treino excluído.")
        return redirect("academia:dashboard")
    return render(request, "academia/confirm_delete.html", {
        "object": record, "object_type": "treino", "cancel_url": "academia:dashboard",
    })
