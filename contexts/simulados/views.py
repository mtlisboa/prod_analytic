from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IntervaloFormSet, MetaForm, MetaMateriaFormSet, SimuladoForm
from .models import Meta, Simulado


@login_required
def dashboard(request):
    simulations = request.user.simulados.prefetch_related("intervals")
    goals = request.user.metas_simulados.prefetch_related("subjects")
    totals = simulations.aggregate(
        correct=Sum("correct_answers"), wrong=Sum("wrong_answers"), time=Sum("total_time_minutes")
    )
    answered = (totals["correct"] or 0) + (totals["wrong"] or 0)
    context = {
        "simulations": simulations,
        "count": simulations.count(),
        "accuracy": round((totals["correct"] or 0) / answered * 100) if answered else 0,
        "total_time": totals["time"] or 0,
        "goals": goals,
        "goals_count": goals.count(),
    }
    return render(request, "simulados/dashboard.html", context)


@login_required
def create(request):
    form = SimuladoForm(request.POST or None, user=request.user)
    formset = IntervaloFormSet(request.POST or None, prefix="intervals")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        interval_total = sum(
            item.get("duration_minutes") or 0
            for item in formset.cleaned_data
            if item and not item.get("DELETE")
        )
        if interval_total and interval_total != form.cleaned_data["rested_time_minutes"]:
            form.add_error(None, "A soma dos intervalos deve ser igual ao tempo descansado informado.")
            return render(request, "simulados/form.html", _simulation_form_context(request, form, formset))
        with transaction.atomic():
            simulado = form.save(commit=False)
            simulado.user = request.user
            simulado.save()
            formset.instance = simulado
            intervals = formset.save(commit=False)
            for position, interval in enumerate(intervals, start=1):
                interval.position = position
                interval.save()
            for interval in formset.deleted_objects:
                if interval.pk:
                    interval.delete()
        messages.success(request, "Simulado registrado com sucesso.")
        return redirect("simulados:dashboard")
    return render(request, "simulados/form.html", _simulation_form_context(request, form, formset))


def _simulation_form_context(request, form, formset):
    goals = request.user.metas_simulados.prefetch_related("subjects")
    goal_subjects = {str(goal.pk): [item.subject for item in goal.subjects.all()] for goal in goals}
    return {"form": form, "formset": formset, "goal_subjects": goal_subjects}


@login_required
def delete(request, pk):
    simulado = get_object_or_404(Simulado, pk=pk, user=request.user)
    if request.method == "POST":
        simulado.delete()
        messages.success(request, "Simulado excluído.")
        return redirect("simulados:dashboard")
    return render(request, "simulados/confirm_delete.html", {"simulado": simulado})


@login_required
def create_goal(request):
    form = MetaForm(request.POST or None)
    formset = MetaMateriaFormSet(request.POST or None, prefix="subjects")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            formset.instance = goal
            subjects = formset.save(commit=False)
            for position, subject in enumerate(subjects, start=1):
                subject.position = position
                subject.save()
        messages.success(request, "Meta adicionada com sucesso.")
        return redirect("simulados:dashboard")
    return render(request, "simulados/goal_form.html", {"form": form, "formset": formset})


@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Meta, pk=pk, user=request.user)
    if request.method == "POST":
        goal.delete()
        messages.success(request, "Meta excluída.")
        return redirect("simulados:dashboard")
    return render(request, "simulados/confirm_goal_delete.html", {"goal": goal})
