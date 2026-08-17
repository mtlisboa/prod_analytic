from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from contexts.academia.features.catalog.models import AdvancedTechnique, Exercise


class TrainingRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="training_records")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="records", verbose_name="exercício")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.exercise} — {self.created_at:%d/%m/%Y}"

    @property
    def sets_count(self):
        return self.sets.count()

    @property
    def execution_time_seconds(self):
        return sum(item.execution_time_seconds for item in self.sets.all())

    @property
    def rest_time_seconds(self):
        return sum(item.rest_time_seconds for item in self.sets.all())

    @property
    def performed_at(self):
        first_set = self.sets.order_by("position").first()
        return first_set.performed_at if first_set else self.created_at


class TrainingSet(models.Model):
    training_record = models.ForeignKey(TrainingRecord, on_delete=models.CASCADE, related_name="sets")
    position = models.PositiveSmallIntegerField("número da série", validators=[MinValueValidator(1)])
    performed_at = models.DateTimeField("data e hora")
    weight_kg = models.DecimalField("peso (kg)", max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    reps = models.PositiveIntegerField("repetições totais", default=0, validators=[MinValueValidator(0)])
    partial_reps = models.PositiveIntegerField("repetições parciais", default=0, validators=[MinValueValidator(0)])
    execution_time_seconds = models.PositiveIntegerField("tempo de execução (segundos)", validators=[MinValueValidator(1)])
    rest_time_seconds = models.PositiveIntegerField("tempo de descanso (segundos)", validators=[MinValueValidator(0)])
    advanced_technique = models.ForeignKey(
        AdvancedTechnique, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="training_sets", verbose_name="técnica avançada",
    )
    notes = models.CharField("observações", max_length=240, blank=True)

    class Meta:
        ordering = ("position",)
        constraints = [
            models.UniqueConstraint(fields=("training_record", "position"), name="unique_set_position"),
            models.CheckConstraint(
                condition=models.Q(partial_reps__lte=models.F("reps")),
                name="partial_reps_lte_reps",
            ),
        ]

    def __str__(self):
        return f"{self.training_record.exercise} — série {self.position}"
