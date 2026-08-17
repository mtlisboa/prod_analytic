from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IntervaloFormSet, SimuladoForm
from .models import Simulado


@login_required
def dashboard(request):
    simulations = request.user.simulados.prefetch_related("intervals")
    totals = simulations.aggregate(
        correct=Sum("correct_answers"), wrong=Sum("wrong_answers"), time=Sum("total_time_minutes")
    )
    answered = (totals["correct"] or 0) + (totals["wrong"] or 0)
    context = {
        "simulations": simulations,
        "count": simulations.count(),
        "accuracy": round((totals["correct"] or 0) / answered * 100) if answered else 0,
        "total_time": totals["time"] or 0,
    }
    return render(request, "simulados/dashboard.html", context)


@login_required
def create(request):
    form = SimuladoForm(request.POST or None)
    formset = IntervaloFormSet(request.POST or None, prefix="intervals")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
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
    return render(request, "simulados/form.html", {"form": form, "formset": formset})


@login_required
def delete(request, pk):
    simulado = get_object_or_404(Simulado, pk=pk, user=request.user)
    if request.method == "POST":
        simulado.delete()
        messages.success(request, "Simulado excluído.")
        return redirect("simulados:dashboard")
    return render(request, "simulados/confirm_delete.html", {"simulado": simulado})
