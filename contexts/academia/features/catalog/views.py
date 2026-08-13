from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import AdvancedTechniqueForm, ExerciseForm


@login_required
def create_exercise(request):
    form = ExerciseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        exercise = form.save(commit=False)
        exercise.user = request.user
        exercise.save()
        messages.success(request, "Exercício adicionado ao catálogo.")
        return redirect("academia:training_create")
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
        return redirect("academia:training_create")
    return render(request, "academia/catalog_form.html", {
        "form": form,
        "title": "Nova técnica avançada",
        "eyebrow": "Catálogo",
        "submit_label": "Salvar técnica",
    })
