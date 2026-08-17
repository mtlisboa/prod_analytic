from django import forms
from django.forms import inlineformset_factory

from .models import Intervalo, Simulado


class SimuladoForm(forms.ModelForm):
    hours = forms.IntegerField(label="Horas", min_value=0, required=False, initial=0)
    minutes = forms.IntegerField(label="Minutos", min_value=0, max_value=59, required=False, initial=0)

    class Meta:
        model = Simulado
        fields = ("title", "exam_url", "exam_date", "total_questions", "correct_answers", "wrong_answers", "observation")
        widgets = {
            "exam_date": forms.DateInput(attrs={"type": "date"}),
            "observation": forms.Textarea(attrs={"rows": 5, "placeholder": "Como você se sentiu? O que foi mais difícil? O que precisa revisar?"}),
            "exam_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["hours"].initial = self.instance.total_time_minutes // 60
            self.fields["minutes"].initial = self.instance.total_time_minutes % 60

    def clean(self):
        cleaned = super().clean()
        correct = cleaned.get("correct_answers") or 0
        wrong = cleaned.get("wrong_answers") or 0
        total = cleaned.get("total_questions") or 0
        if correct + wrong > total:
            raise forms.ValidationError("A soma de acertos e erros não pode superar o total de questões.")
        duration = (cleaned.get("hours") or 0) * 60 + (cleaned.get("minutes") or 0)
        if duration < 1:
            raise forms.ValidationError("Informe um tempo total maior que zero.")
        cleaned["total_time_minutes"] = duration
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_time_minutes = self.cleaned_data["total_time_minutes"]
        if commit:
            instance.save()
        return instance


IntervaloFormSet = inlineformset_factory(
    Simulado,
    Intervalo,
    fields=("duration_minutes", "note", "position"),
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
    widgets={"position": forms.HiddenInput()},
)
