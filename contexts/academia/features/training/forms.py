from django import forms
from django.forms import inlineformset_factory

from .models import TrainingRecord, TrainingSet


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ("exercise",)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["exercise"].queryset = user.exercises.filter(active=True)

    def clean_exercise(self):
        exercise = self.cleaned_data["exercise"]
        if exercise.user_id != self.user.id:
            raise forms.ValidationError("Exercício inválido.")
        return exercise


class TrainingSetForm(forms.ModelForm):
    execution_time_seconds = forms.IntegerField(
        label="Tempo de execução (segundos)", min_value=1,
        widget=forms.NumberInput(attrs={"min": 1, "inputmode": "numeric"}),
    )

    class Meta:
        model = TrainingSet
        fields = ("position", "performed_at", "weight_kg", "execution_time_seconds", "rest_time_seconds", "advanced_technique", "notes")
        widgets = {
            "position": forms.HiddenInput(),
            "performed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "weight_kg": forms.NumberInput(attrs={"min": 0, "step": "0.25", "inputmode": "decimal"}),
            "rest_time_seconds": forms.NumberInput(attrs={"min": 0, "inputmode": "numeric"}),
            "notes": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["performed_at"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["advanced_technique"].queryset = user.advanced_techniques.all()
        self.fields["advanced_technique"].empty_label = "Nenhuma"

    def clean_advanced_technique(self):
        technique = self.cleaned_data.get("advanced_technique")
        if technique and technique.user_id != self.user.id:
            raise forms.ValidationError("Técnica inválida.")
        return technique


TrainingSetFormSet = inlineformset_factory(
    TrainingRecord, TrainingSet, form=TrainingSetForm, extra=2,
    min_num=1, validate_min=True, can_delete=True,
)
