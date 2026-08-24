from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AdvancedTechnique, Exercise, TrainingRecord, TrainingSet


class AcademiaSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner")
        self.other = User.objects.create(username="other")
        self.supino = Exercise.objects.create(user=self.user, name="Supino reto", muscle_group="chest")
        self.remada = Exercise.objects.create(user=self.user, name="Remada baixa", muscle_group="back")
        Exercise.objects.create(user=self.other, name="Supino privado", muscle_group="chest")
        AdvancedTechnique.objects.create(user=self.user, name="Drop set")
        AdvancedTechnique.objects.create(user=self.user, name="Rest pause")
        self.client.force_login(self.user)

    def test_catalog_searches_exercises_and_techniques_by_name(self):
        exercises = self.client.get(reverse("academia:exercise_list"), {"q": "supino"})
        self.assertContains(exercises, "Supino reto")
        self.assertNotContains(exercises, "Remada baixa")
        self.assertNotContains(exercises, "Supino privado")

        techniques = self.client.get(reverse("academia:technique_list"), {"q": "drop"})
        self.assertContains(techniques, "Drop set")
        self.assertNotContains(techniques, "Rest pause")

    def test_training_history_search_returns_matching_exercise_with_actions(self):
        for exercise in (self.supino, self.remada):
            record = TrainingRecord.objects.create(user=self.user, exercise=exercise)
            TrainingSet.objects.create(
                training_record=record, position=1, performed_at=timezone.now(),
                weight_kg=50, reps=10, partial_reps=0,
                execution_time_seconds=30, rest_time_seconds=60,
            )

        response = self.client.get(reverse("academia:training_history"), {"q": "supino"})
        html = response.json()["html"]
        self.assertIn("Supino reto", html)
        self.assertNotIn("Remada baixa", html)
        self.assertIn("Editar", html)
        self.assertIn("Excluir", html)

    def test_training_history_search_has_specific_empty_state(self):
        response = self.client.get(reverse("academia:training_history"), {"q": "inexistente"})
        self.assertIn("Nenhum treino encontrado", response.json()["html"])

    def test_analysis_recent_history_only_shows_last_five_days(self):
        recent = TrainingRecord.objects.create(user=self.user, exercise=self.supino)
        TrainingSet.objects.create(
            training_record=recent, position=1, performed_at=timezone.now() - timedelta(days=2),
            weight_kg=50, reps=10, partial_reps=0,
            execution_time_seconds=30, rest_time_seconds=60,
        )
        old = TrainingRecord.objects.create(user=self.user, exercise=self.remada)
        TrainingSet.objects.create(
            training_record=old, position=1, performed_at=timezone.now() - timedelta(days=6),
            weight_kg=50, reps=10, partial_reps=0,
            execution_time_seconds=30, rest_time_seconds=60,
        )

        response = self.client.get(reverse("academia:dashboard"))
        self.assertContains(response, "Supino reto")
        self.assertNotContains(response, "Remada baixa")
