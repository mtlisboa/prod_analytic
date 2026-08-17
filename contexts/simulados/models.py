import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


subject_validator = RegexValidator(
    regex=r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+$",
    message="Use apenas letras sem acentos, números e espaços.",
)


def normalize_subject_value(value):
    decomposed = unicodedata.normalize("NFKD", value or "")
    ascii_value = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(ascii_value.upper().split())


class Simulado(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="simulados")
    title = models.CharField("nome do simulado", max_length=180)
    exam_date = models.DateField("data de realização")
    exam_url = models.URLField("link da prova", blank=True)
    meta = models.ForeignKey(
        "Meta", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="simulations", verbose_name="prova visada",
    )
    subject = models.CharField("matéria", max_length=120, validators=[subject_validator], default="GERAL")
    total_questions = models.PositiveIntegerField("total de questões", validators=[MinValueValidator(1)])
    correct_answers = models.PositiveIntegerField("questões acertadas", default=0)
    wrong_answers = models.PositiveIntegerField("questões erradas", default=0)
    observation = models.TextField("impressões sobre a prova", blank=True)
    total_time_minutes = models.PositiveIntegerField("tempo total (minutos)", validators=[MinValueValidator(1)])
    effective_time_minutes = models.PositiveIntegerField("tempo efetivo (minutos)", validators=[MinValueValidator(1)])
    rested_time_minutes = models.PositiveIntegerField("tempo descansado (minutos)", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-exam_date", "-created_at")

    def clean(self):
        if self.correct_answers + self.wrong_answers > self.total_questions:
            raise ValidationError("A soma de acertos e erros não pode superar o total de questões.")
        if None not in (self.effective_time_minutes, self.rested_time_minutes, self.total_time_minutes) and self.effective_time_minutes + self.rested_time_minutes != self.total_time_minutes:
            raise ValidationError("O tempo total deve ser igual ao tempo efetivo somado ao tempo descansado.")
        self.subject = normalize_subject_value(self.subject)
        if self.meta_id and not self.meta.subjects.filter(subject=self.subject).exists():
            raise ValidationError({"subject": "Selecione uma matéria cadastrada na meta escolhida."})

    @property
    def accuracy(self):
        answered = self.correct_answers + self.wrong_answers
        return round(self.correct_answers / answered * 100) if answered else 0

    @property
    def breaks_time_minutes(self):
        return sum(item.duration_minutes for item in self.intervals.all())

    def __str__(self):
        return f"{self.title} — {self.exam_date:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        self.subject = normalize_subject_value(self.subject)
        super().save(*args, **kwargs)


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


class Meta(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="metas_simulados")
    exam_name = models.CharField("prova", max_length=180)
    exam_date = models.DateField("data da prova", null=True, blank=True)
    exam_time_minutes = models.PositiveIntegerField("tempo-alvo de prova (minutos)", validators=[MinValueValidator(1)])
    break_time_minutes = models.PositiveIntegerField("tempo-alvo de descanso (minutos)", default=0)
    observation = models.TextField("observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (models.F("exam_date").asc(nulls_last=True), "-created_at")

    def __str__(self):
        return self.exam_name


class MetaMateria(models.Model):
    meta = models.ForeignKey(Meta, on_delete=models.CASCADE, related_name="subjects")
    subject = models.CharField("matéria", max_length=120, validators=[subject_validator])
    target_accuracy_percent = models.PositiveSmallIntegerField(
        "aproveitamento-alvo (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    position = models.PositiveSmallIntegerField("ordem", validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("position",)
        constraints = [models.UniqueConstraint(fields=("meta", "position"), name="unique_meta_subject_position")]

    def __str__(self):
        return f"{self.subject}: {self.target_accuracy_percent}%"

    def save(self, *args, **kwargs):
        self.subject = normalize_subject_value(self.subject)
        super().save(*args, **kwargs)
