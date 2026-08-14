from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AdvancedTechnique, Exercise, TrainingRecord, TrainingSet


class AcademiaFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="matheus", password="senha-segura-123")
        self.other = User.objects.create_user(username="outro", password="senha-segura-123")
        self.exercise = Exercise.objects.create(user=self.user, name="Supino", muscle_group="chest")
        self.technique = AdvancedTechnique.objects.create(user=self.user, name="Drop set")
        self.client.force_login(self.user)

    def test_training_record_creation(self):
        response = self.client.post(reverse("academia:training_create"), {
            "exercise": self.exercise.pk,
            "sets-TOTAL_FORMS": 2, "sets-INITIAL_FORMS": 0, "sets-MIN_NUM_FORMS": 1, "sets-MAX_NUM_FORMS": 1000,
            "sets-0-position": 1, "sets-0-performed_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "sets-0-weight_kg": "80.00", "sets-0-execution_time_seconds": 40, "sets-0-rest_time_seconds": 60,
            "sets-0-advanced_technique": self.technique.pk, "sets-0-notes": "Bom controle",
            "sets-1-position": 2, "sets-1-performed_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "sets-1-weight_kg": "82.00", "sets-1-execution_time_seconds": 42, "sets-1-rest_time_seconds": 75,
            "sets-1-advanced_technique": "", "sets-1-notes": "",
        })
        self.assertRedirects(response, reverse("academia:dashboard"))
        self.assertEqual(TrainingRecord.objects.get().user, self.user)
        self.assertEqual(TrainingSet.objects.count(), 2)
        self.assertEqual(list(TrainingSet.objects.values_list("rest_time_seconds", flat=True)), [60, 75])

    def test_training_form_starts_with_three_editable_sets_and_modal(self):
        response = self.client.get(reverse("academia:training_create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["formset"].total_form_count(), 3)
        self.assertContains(response, 'id="set-modal"')
        self.assertContains(response, 'name="sets-2-rest_time_seconds"')

    def test_dashboard_filters_and_aggregates(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(training_record=record, position=1, performed_at=timezone.now(), weight_kg=80, execution_time_seconds=40, rest_time_seconds=60)
        TrainingSet.objects.create(training_record=record, position=2, performed_at=timezone.now(), weight_kg=80, execution_time_seconds=40, rest_time_seconds=90)
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse("academia:dashboard"), {"start_date": today, "end_date": today, "period": "daily", "metric": "rest_per_set", "technique": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "75.0")

    def test_dashboard_accepts_multiple_time_metrics_and_custom_axes(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, execution_time_seconds=40, rest_time_seconds=60,
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse("academia:dashboard"), {
            "start_date": today,
            "end_date": today,
            "period": "daily",
            "metrics": ["sets", "weight_per_set"],
            "exercises": [self.exercise.pk],
            "x_axis": "set_position",
            "y_axis": "weight",
            "group_by": "exercise",
            "technique": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["key"] for item in response.context["chart_series"]],
            [f"sets-{self.exercise.pk}", f"weight_per_set-{self.exercise.pk}"],
        )
        self.assertContains(response, "Força / carga em função de Número da série")
        self.assertContains(response, '"x": 1, "y": 80.0')
        self.assertEqual(response.context["comparison"]["series"][0]["label"], "Supino")

    def test_dynamic_chart_accepts_categories_on_either_axis(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, execution_time_seconds=40, rest_time_seconds=60,
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse("academia:dashboard"), {
            "start_date": today, "end_date": today, "period": "daily",
            "metrics": ["sets"], "exercises": [self.exercise.pk],
            "x_axis": "weight", "y_axis": "exercise", "group_by": "",
            "technique": "",
        })

        comparison = response.context["comparison"]
        self.assertEqual(comparison["x"]["kind"], "number")
        self.assertEqual(comparison["y"]["kind"], "category")
        self.assertEqual(comparison["series"][0]["points"], [{"x": 80.0, "y": "Supino"}])

    def test_user_cannot_select_another_users_exercise(self):
        private_exercise = Exercise.objects.create(user=self.other, name="Agachamento", muscle_group="legs")
        response = self.client.post(reverse("academia:training_create"), {
            "exercise": private_exercise.pk,
            "sets-TOTAL_FORMS": 1, "sets-INITIAL_FORMS": 0, "sets-MIN_NUM_FORMS": 1, "sets-MAX_NUM_FORMS": 1000,
            "sets-0-position": 1, "sets-0-performed_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "sets-0-weight_kg": 30, "sets-0-execution_time_seconds": 30, "sets-0-rest_time_seconds": 40,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TrainingRecord.objects.exists())

    def test_exercise_search_filters_in_database_and_by_user(self):
        Exercise.objects.create(user=self.user, name="Supino inclinado", muscle_group="chest")
        Exercise.objects.create(user=self.user, name="Agachamento", muscle_group="legs")
        Exercise.objects.create(user=self.other, name="Supino privado", muscle_group="chest")

        response = self.client.get(reverse("academia:exercise_search"), {"q": "supino"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["name"] for item in response.json()["results"]],
            ["Supino", "Supino inclinado"],
        )

    def test_exercise_search_does_not_return_everything_for_empty_query(self):
        response = self.client.get(reverse("academia:exercise_search"), {"q": ""})
        self.assertEqual(response.json(), {"results": []})

    def test_catalog_items_can_be_updated_and_deleted(self):
        response = self.client.post(reverse("academia:exercise_update", args=[self.exercise.pk]), {
            "name": "Supino reto", "muscle_group": "chest",
        })
        self.assertRedirects(response, reverse("academia:exercise_list"))
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.name, "Supino reto")

        response = self.client.post(reverse("academia:technique_delete", args=[self.technique.pk]))
        self.assertRedirects(response, reverse("academia:technique_list"))
        self.assertFalse(AdvancedTechnique.objects.filter(pk=self.technique.pk).exists())

    def test_exercise_with_training_history_cannot_be_deleted(self):
        TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        response = self.client.post(reverse("academia:exercise_delete", args=[self.exercise.pk]), follow=True)
        self.assertTrue(Exercise.objects.filter(pk=self.exercise.pk).exists())
        self.assertContains(response, "não pode ser excluído")

    def test_training_can_be_updated_and_deleted(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        training_set = TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, execution_time_seconds=40, rest_time_seconds=60,
        )
        performed_at = timezone.localtime(training_set.performed_at).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("academia:training_update", args=[record.pk]), {
            "exercise": self.exercise.pk,
            "sets-TOTAL_FORMS": 1, "sets-INITIAL_FORMS": 1,
            "sets-MIN_NUM_FORMS": 1, "sets-MAX_NUM_FORMS": 1000,
            "sets-0-id": training_set.pk, "sets-0-position": 1,
            "sets-0-performed_at": performed_at, "sets-0-weight_kg": "85.00",
            "sets-0-execution_time_seconds": 42, "sets-0-rest_time_seconds": 70,
            "sets-0-advanced_technique": "", "sets-0-notes": "Atualizado",
        })
        self.assertRedirects(response, reverse("academia:dashboard"))
        training_set.refresh_from_db()
        self.assertEqual(str(training_set.weight_kg), "85.00")

        response = self.client.post(reverse("academia:training_delete", args=[record.pk]))
        self.assertRedirects(response, reverse("academia:dashboard"))
        self.assertFalse(TrainingRecord.objects.filter(pk=record.pk).exists())
        self.assertFalse(TrainingSet.objects.filter(pk=training_set.pk).exists())

    def test_user_cannot_manage_another_users_objects(self):
        other_exercise = Exercise.objects.create(user=self.other, name="Remada", muscle_group="back")
        other_record = TrainingRecord.objects.create(user=self.other, exercise=other_exercise)
        protected_urls = (
            reverse("academia:exercise_update", args=[other_exercise.pk]),
            reverse("academia:exercise_delete", args=[other_exercise.pk]),
            reverse("academia:training_update", args=[other_record.pk]),
            reverse("academia:training_delete", args=[other_record.pk]),
        )
        for url in protected_urls:
            self.assertEqual(self.client.get(url).status_code, 404)


class SingleUserRegistrationTests(TestCase):
    def test_signup_creates_the_first_account(self):
        response = self.client.post(reverse("manager:signup"), {
            "username": "dono",
            "email": "dono@example.com",
            "password1": "uma-senha-bem-segura-123",
            "password2": "uma-senha-bem-segura-123",
        })
        self.assertRedirects(response, reverse("academia:dashboard"))
        self.assertEqual(User.objects.count(), 1)

    def test_signup_is_blocked_after_first_account(self):
        User.objects.create_user(username="dono", password="senha-segura-123")
        response = self.client.get(reverse("manager:signup"))
        self.assertRedirects(response, reverse("manager:login"))
