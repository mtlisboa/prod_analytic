from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Simulado(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="simulados")
    title = models.CharField("nome do simulado", max_length=180)
    exam_date = models.DateField("data de realização")
    exam_url = models.URLField("link da prova", blank=True)
    total_questions = models.PositiveIntegerField("total de questões", validators=[MinValueValidator(1)])
    correct_answers = models.PositiveIntegerField("questões acertadas", default=0)
    wrong_answers = models.PositiveIntegerField("questões erradas", default=0)
    observation = models.TextField("impressões sobre a prova", blank=True)
    total_time_minutes = models.PositiveIntegerField("tempo total (minutos)", validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-exam_date", "-created_at")

    def clean(self):
        if self.correct_answers + self.wrong_answers > self.total_questions:
            raise ValidationError("A soma de acertos e erros não pode superar o total de questões.")

    @property
    def accuracy(self):
        answered = self.correct_answers + self.wrong_answers
        return round(self.correct_answers / answered * 100) if answered else 0

    @property
    def breaks_time_minutes(self):
        return sum(item.duration_minutes for item in self.intervals.all())

    def __str__(self):
        return f"{self.title} — {self.exam_date:%d/%m/%Y}"


class Intervalo(models.Model):
    simulado = models.ForeignKey(Simulado, on_delete=models.CASCADE, related_name="intervals")
    position = models.PositiveSmallIntegerField("ordem", validators=[MinValueValidator(1)])
    duration_minutes = models.PositiveIntegerField("duração (minutos)", validators=[MinValueValidator(1)])
    note = models.CharField("observação", max_length=180, blank=True)

    class Meta:
        ordering = ("position",)
        constraints = [models.UniqueConstraint(fields=("simulado", "position"), name="unique_simulado_interval_position")]

    def __str__(self):
        return f"Intervalo {self.position} — {self.duration_minutes} min"
