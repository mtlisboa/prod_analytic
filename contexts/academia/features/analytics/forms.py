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

    start_date = forms.DateField(label="De", widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label="Até", widget=forms.DateInput(attrs={"type": "date"}))
    period = forms.ChoiceField(label="Agrupar por", choices=PERIOD_CHOICES)
    metric = forms.ChoiceField(label="Variável", choices=METRIC_CHOICES)
    technique = forms.ModelChoiceField(label="Técnica", queryset=None, required=False, empty_label="Todas")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["technique"].queryset = user.advanced_techniques.all()
        self.fields["start_date"].initial = today.replace(day=1)
        self.fields["end_date"].initial = today
        self.fields["period"].initial = "daily"
        self.fields["metric"].initial = "sets"

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "A data final deve ser posterior à inicial.")
        return cleaned
