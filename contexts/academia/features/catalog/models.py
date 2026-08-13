from django.conf import settings
from django.db import models


class Exercise(models.Model):
    class MuscleGroup(models.TextChoices):
        CHEST = "chest", "Peito"
        BACK = "back", "Costas"
        LEGS = "legs", "Pernas"
        SHOULDERS = "shoulders", "Ombros"
        ARMS = "arms", "Braços"
        CORE = "core", "Core"
        CARDIO = "cardio", "Cardio"
        OTHER = "other", "Outro"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercises")
    name = models.CharField("nome", max_length=100)
    muscle_group = models.CharField("grupo muscular", max_length=20, choices=MuscleGroup.choices)
    active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [models.UniqueConstraint(fields=("user", "name"), name="unique_exercise_per_user")]

    def __str__(self):
        return self.name


class AdvancedTechnique(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="advanced_techniques")
    name = models.CharField("nome", max_length=100)
    description = models.TextField("descrição", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [models.UniqueConstraint(fields=("user", "name"), name="unique_technique_per_user")]

    def __str__(self):
        return self.name
