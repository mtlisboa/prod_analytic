from django import forms
from django.utils import timezone


class AnalyticsFilterForm(forms.Form):
    PERIOD_CHOICES = (
        ("daily", "Diário"),
        ("weekly", "Semanal"),
        ("monthly", "Mensal"),
    )
    METRIC_CHOICES = (
        ("sets", "Número de séries"),
        ("rest_time", "Tempo total de descanso"),
        ("weight_per_set", "Peso por série"),
        ("rest_per_set", "Tempo de descanso por série"),
        ("execution_per_set", "Tempo de execução por série"),
    )
    AXIS_CHOICES = (
        ("exercise", "Exercício"),
        ("set_position", "Número da série"),
        ("weight", "Força / carga"),
        ("execution", "Tempo de execução"),
        ("rest", "Tempo de descanso"),
        ("technique", "Técnica"),
        ("date", "Data"),
    )
    GROUP_CHOICES = (
        ("", "Sem agrupamento"),
        ("exercise", "Exercício"),
        ("technique", "Técnica"),
    )

    start_date = forms.DateField(label="De", widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label="Até", widget=forms.DateInput(attrs={"type": "date"}))
    period = forms.ChoiceField(label="Agrupar por", choices=PERIOD_CHOICES)
    metrics = forms.MultipleChoiceField(
        label="Linhas do gráfico temporal (eixo Y)",
        choices=METRIC_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text="O eixo X deste gráfico é sempre o tempo.",
    )
    exercises = forms.ModelMultipleChoiceField(
        label="Exercícios no gráfico temporal",
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Cada exercício e variável selecionados formam uma linha.",
    )
    x_axis = forms.ChoiceField(label="Eixo X (gráfico dinâmico)", choices=AXIS_CHOICES)
    y_axis = forms.ChoiceField(label="Eixo Y (gráfico dinâmico)", choices=AXIS_CHOICES)
    group_by = forms.ChoiceField(label="Separar linhas por", choices=GROUP_CHOICES, required=False)
    technique = forms.ModelChoiceField(label="Técnica", queryset=None, required=False, empty_label="Todas")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["technique"].queryset = user.advanced_techniques.all()
        self.fields["exercises"].queryset = user.exercises.filter(active=True)
        self.fields["start_date"].initial = today.replace(day=1)
        self.fields["end_date"].initial = today
        self.fields["period"].initial = "daily"
        self.fields["metrics"].initial = [key for key, _label in self.METRIC_CHOICES]
        self.fields["exercises"].initial = user.exercises.filter(active=True)
        self.fields["x_axis"].initial = "set_position"
        self.fields["y_axis"].initial = "weight"
        self.fields["group_by"].initial = "exercise"

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "A data final deve ser posterior à inicial.")
        return cleaned
