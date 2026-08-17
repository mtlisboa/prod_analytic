from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Intervalo, Meta, MetaMateria, Simulado, normalize_subject_value, subject_validator


def normalize_subject(value):
    return normalize_subject_value(value)


class SimuladoForm(forms.ModelForm):
    total_hours = forms.IntegerField(label="Horas totais", min_value=0, required=False, initial=0)
    total_minutes = forms.IntegerField(label="Minutos totais", min_value=0, max_value=59, required=False, initial=0)
    effective_hours = forms.IntegerField(label="Horas efetivas", min_value=0, required=False, initial=0)
    effective_minutes = forms.IntegerField(label="Minutos efetivos", min_value=0, max_value=59, required=False, initial=0)
    rested_hours = forms.IntegerField(label="Horas descansadas", min_value=0, required=False, initial=0)
    rested_minutes = forms.IntegerField(label="Minutos descansados", min_value=0, max_value=59, required=False, initial=0)

    class Meta:
        model = Simulado
        fields = ("meta", "subject", "title", "exam_url", "exam_date", "total_questions", "correct_answers", "wrong_answers", "observation")
        widgets = {
            "exam_date": forms.DateInput(attrs={"type": "date"}),
            "observation": forms.Textarea(attrs={"rows": 5, "placeholder": "Como você se sentiu? O que foi mais difícil? O que precisa revisar?"}),
            "exam_url": forms.URLInput(attrs={"placeholder": "https://..."}),
            "subject": forms.TextInput(attrs={"list": "subject-options", "autocomplete": "off", "data-subject-input": "", "placeholder": "EX.: PORTUGUES"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["meta"].queryset = Meta.objects.filter(user=user) if user else Meta.objects.none()
        self.fields["meta"].empty_label = "Sem meta vinculada"
        if self.instance and self.instance.pk:
            for prefix, value in (("total", self.instance.total_time_minutes), ("effective", self.instance.effective_time_minutes), ("rested", self.instance.rested_time_minutes)):
                self.fields[f"{prefix}_hours"].initial = value // 60
                self.fields[f"{prefix}_minutes"].initial = value % 60

    def clean_subject(self):
        value = normalize_subject(self.cleaned_data.get("subject"))
        subject_validator(value)
        return value

    def clean(self):
        cleaned = super().clean()
        correct = cleaned.get("correct_answers") or 0
        wrong = cleaned.get("wrong_answers") or 0
        total = cleaned.get("total_questions") or 0
        if correct + wrong > total:
            raise forms.ValidationError("A soma de acertos e erros não pode superar o total de questões.")
        total = (cleaned.get("total_hours") or 0) * 60 + (cleaned.get("total_minutes") or 0)
        effective = (cleaned.get("effective_hours") or 0) * 60 + (cleaned.get("effective_minutes") or 0)
        rested = (cleaned.get("rested_hours") or 0) * 60 + (cleaned.get("rested_minutes") or 0)
        if total < 1 or effective < 1:
            raise forms.ValidationError("Informe um tempo total maior que zero.")
        if effective + rested != total:
            raise forms.ValidationError("O tempo total deve ser igual ao tempo efetivo somado ao tempo descansado.")
        meta = cleaned.get("meta")
        subject = cleaned.get("subject")
        if meta and subject and not meta.subjects.filter(subject=subject).exists():
            self.add_error("subject", "Selecione uma matéria cadastrada na meta escolhida.")
        cleaned["total_time_minutes"] = total
        cleaned["effective_time_minutes"] = effective
        cleaned["rested_time_minutes"] = rested
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_time_minutes = self.cleaned_data["total_time_minutes"]
        instance.effective_time_minutes = self.cleaned_data["effective_time_minutes"]
        instance.rested_time_minutes = self.cleaned_data["rested_time_minutes"]
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


class MetaForm(forms.ModelForm):
    exam_hours = forms.IntegerField(label="Horas de prova", min_value=0, required=False, initial=0)
    exam_minutes = forms.IntegerField(label="Minutos de prova", min_value=0, max_value=59, required=False, initial=0)
    break_hours = forms.IntegerField(label="Horas de descanso", min_value=0, required=False, initial=0)
    break_minutes = forms.IntegerField(label="Minutos de descanso", min_value=0, max_value=59, required=False, initial=0)

    class Meta:
        model = Meta
        fields = ("exam_name", "exam_date", "observation")
        widgets = {
            "exam_date": forms.DateInput(attrs={"type": "date"}),
            "observation": forms.Textarea(attrs={"rows": 4, "placeholder": "Estratégia, edital, observações importantes..."}),
        }

    def clean(self):
        cleaned = super().clean()
        exam_time = (cleaned.get("exam_hours") or 0) * 60 + (cleaned.get("exam_minutes") or 0)
        break_time = (cleaned.get("break_hours") or 0) * 60 + (cleaned.get("break_minutes") or 0)
        if exam_time < 1:
            raise forms.ValidationError("Informe um tempo-alvo de prova maior que zero.")
        cleaned["exam_time_minutes"] = exam_time
        cleaned["break_time_minutes"] = break_time
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.exam_time_minutes = self.cleaned_data["exam_time_minutes"]
        instance.break_time_minutes = self.cleaned_data["break_time_minutes"]
        if commit:
            instance.save()
        return instance


class MetaMateriaForm(forms.ModelForm):
    class Meta:
        model = MetaMateria
        fields = ("subject", "target_accuracy_percent", "position")
        widgets = {
            "position": forms.HiddenInput(),
            "subject": forms.TextInput(attrs={"data-uppercase-subject": "", "autocomplete": "off", "placeholder": "EX.: MATEMATICA"}),
        }

    def clean_subject(self):
        value = normalize_subject(self.cleaned_data.get("subject"))
        subject_validator(value)
        return value


class BaseMetaMateriaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        subjects = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                subject = form.cleaned_data.get("subject")
                if subject in subjects:
                    raise forms.ValidationError("Cada matéria pode aparecer apenas uma vez na meta.")
                subjects.append(subject)


MetaMateriaFormSet = inlineformset_factory(
    Meta,
    MetaMateria,
    form=MetaMateriaForm,
    formset=BaseMetaMateriaFormSet,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
    widgets={"position": forms.HiddenInput()},
)
