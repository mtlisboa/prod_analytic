from django import forms
from django.forms import inlineformset_factory

from .models import TrainingRecord, TrainingSet


class ExerciseSearchSelect(forms.Select):
    def use_required_attribute(self, initial):
        return False


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ("exercise",)
        widgets = {"exercise": ExerciseSearchSelect()}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        exercise_id = self.data.get("exercise") if self.is_bound else self.initial.get("exercise")
        if not exercise_id and self.instance and self.instance.exercise_id:
            exercise_id = self.instance.exercise_id
        self.fields["exercise"].queryset = user.exercises.filter(active=True, pk=exercise_id)
        self.fields["exercise"].widget.attrs["class"] = "exercise-native-select"

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
        fields = (
            "position", "performed_at", "weight_kg", "reps", "partial_reps",
            "execution_time_seconds", "rest_time_seconds", "advanced_technique", "notes",
        )
        widgets = {
            "position": forms.HiddenInput(),
            "performed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "weight_kg": forms.NumberInput(attrs={"min": 0, "step": "0.25", "inputmode": "decimal"}),
            "reps": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric"}),
            "partial_reps": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric"}),
            "rest_time_seconds": forms.NumberInput(attrs={"min": 0, "inputmode": "numeric"}),
            "notes": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["performed_at"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["advanced_technique"].queryset = user.advanced_techniques.all()
        self.fields["advanced_technique"].empty_label = "Nenhuma"

    def clean(self):
        cleaned_data = super().clean()
        reps = cleaned_data.get("reps")
        partial_reps = cleaned_data.get("partial_reps")
        if reps is not None and partial_reps is not None and partial_reps > reps:
            self.add_error(
                "partial_reps",
                "As repetições parciais não podem ser maiores que o total de repetições.",
            )
        return cleaned_data

    def clean_advanced_technique(self):
        technique = self.cleaned_data.get("advanced_technique")
        if technique and technique.user_id != self.user.id:
            raise forms.ValidationError("Técnica inválida.")
        return technique


TrainingSetCreateFormSet = inlineformset_factory(
    # The create view supplies the single initial set. Keeping ``extra`` at 1
    # rendered a second blank form; the JavaScript renumbered it and Django
    # consequently treated it as changed, rejecting the whole submission.
    TrainingRecord, TrainingSet, form=TrainingSetForm, extra=0,
    min_num=1, validate_min=True, can_delete=True,
)

TrainingSetUpdateFormSet = inlineformset_factory(
    TrainingRecord, TrainingSet, form=TrainingSetForm, extra=0,
    min_num=1, validate_min=True, can_delete=True,
)
