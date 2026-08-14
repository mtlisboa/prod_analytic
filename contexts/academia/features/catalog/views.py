from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdvancedTechniqueForm, ExerciseForm
from .models import AdvancedTechnique, Exercise


@login_required
def exercise_list(request):
    return render(request, "academia/catalog_list.html", {
        "items": request.user.exercises.all(), "kind": "exercise",
        "title": "Exercícios", "create_url": "academia:exercise_create",
    })


@login_required
def technique_list(request):
    return render(request, "academia/catalog_list.html", {
        "items": request.user.advanced_techniques.all(), "kind": "technique",
        "title": "Técnicas avançadas", "create_url": "academia:technique_create",
    })


@login_required
def create_exercise(request):
    form = ExerciseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        exercise = form.save(commit=False)
        exercise.user = request.user
        exercise.save()
        messages.success(request, "Exercício adicionado ao catálogo.")
        return redirect("academia:exercise_list")
    return render(request, "academia/catalog_form.html", {
        "form": form,
        "title": "Novo exercício",
        "eyebrow": "Catálogo",
        "submit_label": "Salvar exercício",
    })


@login_required
def create_technique(request):
    form = AdvancedTechniqueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        technique = form.save(commit=False)
        technique.user = request.user
        technique.save()
        messages.success(request, "Técnica avançada adicionada.")
        return redirect("academia:technique_list")
    return render(request, "academia/catalog_form.html", {
        "form": form,
        "title": "Nova técnica avançada",
        "eyebrow": "Catálogo",
        "submit_label": "Salvar técnica",
    })


@login_required
def update_exercise(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    form = ExerciseForm(request.POST or None, instance=exercise)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Exercício atualizado.")
        return redirect("academia:exercise_list")
    return render(request, "academia/catalog_form.html", {
        "form": form, "title": "Editar exercício", "eyebrow": "Catálogo",
        "submit_label": "Salvar alterações",
    })


@login_required
def update_technique(request, pk):
    technique = get_object_or_404(AdvancedTechnique, pk=pk, user=request.user)
    form = AdvancedTechniqueForm(request.POST or None, instance=technique)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Técnica atualizada.")
        return redirect("academia:technique_list")
    return render(request, "academia/catalog_form.html", {
        "form": form, "title": "Editar técnica avançada", "eyebrow": "Catálogo",
        "submit_label": "Salvar alterações",
    })


def _delete_catalog_item(request, *, model, pk, label, redirect_name):
    item = get_object_or_404(model, pk=pk, user=request.user)
    if request.method == "POST":
        try:
            item.delete()
            messages.success(request, f"{label} excluído(a).")
        except ProtectedError:
            messages.error(request, "Este exercício possui treinos e não pode ser excluído.")
        return redirect(redirect_name)
    return render(request, "academia/confirm_delete.html", {
        "object": item, "object_type": label.lower(), "cancel_url": redirect_name,
    })


@login_required
def delete_exercise(request, pk):
    return _delete_catalog_item(request, model=Exercise, pk=pk, label="Exercício", redirect_name="academia:exercise_list")


@login_required
def delete_technique(request, pk):
    return _delete_catalog_item(request, model=AdvancedTechnique, pk=pk, label="Técnica", redirect_name="academia:technique_list")
