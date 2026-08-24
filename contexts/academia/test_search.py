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
        self.assertEqual([item.name for item in exercises.context["items"]], ["Supino reto"])

        techniques = self.client.get(reverse("academia:technique_list"), {"q": "drop"})
        self.assertEqual([item.name for item in techniques.context["items"]], ["Drop set"])

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

    def test_academia_pages_expose_training_registration_as_modal(self):
        response = self.client.get(reverse("academia:dashboard"))
        self.assertContains(response, 'id="training-create-modal"')
        self.assertContains(response, "data-training-modal-open")
        self.assertContains(response, "data-training-modal-form")

    def test_training_modal_submits_asynchronously_and_returns_validation(self):
        performed_at = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        payload = {
            "exercise": self.supino.pk,
            "sets-TOTAL_FORMS": 1,
            "sets-INITIAL_FORMS": 0,
            "sets-MIN_NUM_FORMS": 1,
            "sets-MAX_NUM_FORMS": 1000,
            "sets-0-position": 1,
            "sets-0-performed_at": performed_at,
            "sets-0-weight_kg": "60.00",
            "sets-0-reps": 10,
            "sets-0-partial_reps": 0,
            "sets-0-execution_time_seconds": 30,
            "sets-0-rest_time_seconds": 60,
            "sets-0-advanced_technique": "",
            "sets-0-notes": "",
        }
        response = self.client.post(
            reverse("academia:training_create"), payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(TrainingRecord.objects.filter(user=self.user, exercise=self.supino).exists())

        payload["sets-0-weight_kg"] = ""
        invalid = self.client.post(
            reverse("academia:training_create"), payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(invalid.status_code, 422)
        self.assertContains(invalid, "O treino não foi salvo", status_code=422)
