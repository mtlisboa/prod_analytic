from django import forms

from .models import AdvancedTechnique, Exercise


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ("name", "muscle_group")


class AdvancedTechniqueForm(forms.ModelForm):
    class Meta:
        model = AdvancedTechnique
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
