from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from .forms import (
    TrainingRecordForm,
    TrainingSetCreateFormSet,
    TrainingSetUpdateFormSet,
)
from .models import TrainingRecord
from .queries import HISTORY_PAGE_SIZE, training_history_queryset


@login_required
def training_list(request):
    records = training_history_queryset(request.user)
    history_page = Paginator(records, HISTORY_PAGE_SIZE).get_page(1)
    return render(request, "academia/training_list.html", {"history_page": history_page})


@login_required
def training_history(request):
    query = request.GET.get("q", "").strip()[:100]
    paginator = Paginator(training_history_queryset(request.user, query), HISTORY_PAGE_SIZE)
    try:
        page_number = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Página inválida."}, status=400)

    if page_number < 1:
        return JsonResponse({"detail": "Página inválida."}, status=400)

    try:
        page = paginator.page(page_number)
    except EmptyPage:
        return JsonResponse({"html": "", "has_next": False, "next_page": None})

    return JsonResponse({
        "html": render_to_string(
            "academia/_training_history_rows.html",
            {
                "records": page.object_list,
                "empty_message": "Nenhum treino encontrado para esta busca.",
            },
            request=request,
        ),
        "has_next": page.has_next(),
        "next_page": page.next_page_number() if page.has_next() else None,
    })


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
    initial = [{
        "position": 1,
        "performed_at": now,
        "reps": 0,
        "partial_reps": 0,
        "execution_time_seconds": 1,
        "rest_time_seconds": 60,
    }]
    formset = TrainingSetCreateFormSet(
        request.POST or None,
        instance=record,
        prefix="sets",
        form_kwargs={"user": request.user},
        initial=initial if request.method != "POST" else None,
    )
    if request.method == "POST":
        form_is_valid = form.is_valid()
        formset_is_valid = formset.is_valid()
    else:
        form_is_valid = formset_is_valid = False

    if form_is_valid and formset_is_valid:
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
    if request.method == "POST":
        form_is_valid = form.is_valid()
        formset_is_valid = formset.is_valid()
    else:
        form_is_valid = formset_is_valid = False

    if form_is_valid and formset_is_valid:
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
