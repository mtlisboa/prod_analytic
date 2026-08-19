import json
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

    def _graphql(self, query, variables=None):
        return self.client.post(
            reverse("analytics_graphql:endpoint"),
            data=json.dumps({"query": query, "variables": variables or {}}),
            content_type="application/json",
        )

    def test_dashboard_loads_the_graphql_analysis_builder(self):
        response = self.client.get(reverse("academia:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("analytics_graphql:endpoint"))
        self.assertContains(response, 'id="analysis-fields"')
        self.assertContains(response, 'id="x-function"')
        self.assertContains(response, 'id="comparison-lines"')
        self.assertContains(response, 'id="add-comparison-line"')

    def test_graphql_endpoint_requires_authentication(self):
        self.client.logout()
        response = self._graphql("query { analysisFields { key } }")
        self.assertEqual(response.status_code, 302)

    def test_graphql_lists_fields_and_only_the_users_catalog(self):
        Exercise.objects.create(user=self.other, name="Privado", muscle_group="legs")
        response = self._graphql("""
            query { analysisFields { key label supportedFunctions { key } }
                    analysisCatalog { exercises { id name } techniques { id name } } }
        """)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("WEIGHT", [item["key"] for item in data["analysisFields"]])
        field_keys = [item["key"] for item in data["analysisFields"]]
        self.assertIn("REPS", field_keys)
        self.assertIn("PARTIAL_REPS", field_keys)
        self.assertIn("PARTIAL_REPS_RATIO", field_keys)
        self.assertIn("NON_PARTIAL_REPS", field_keys)
        self.assertEqual([item["name"] for item in data["analysisCatalog"]["exercises"]], ["Supino"])

    def test_graphql_time_analysis_accepts_multiple_lines_and_classes(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, reps=8, partial_reps=2, execution_time_seconds=40, rest_time_seconds=60,
            advanced_technique=self.technique,
        )
        TrainingSet.objects.create(
            training_record=record, position=2, performed_at=timezone.now(),
            weight_kg=90, reps=10, partial_reps=4, execution_time_seconds=42, rest_time_seconds=90,
            advanced_technique=self.technique,
        )
        today = timezone.localdate().isoformat()
        response = self._graphql("""
            query($input: TimeAnalysisInput!) {
              timeAnalysis(input: $input) { series { label points { x y } } }
            }
        """, {"input": {
            "startDate": today, "endDate": today, "period": "DAILY",
            "lines": [
                {"field": "WEIGHT", "function": "AVG"},
                {"field": "REST", "function": "SUM"},
                {"field": "REPS", "function": "SUM"},
                {"field": "PARTIAL_REPS", "function": "SUM"},
                {"field": "PARTIAL_REPS_RATIO", "function": "AVG"},
                {"field": "NON_PARTIAL_REPS", "function": "SUM"}
            ],
            "groupBy": ["EXERCISE", "TECHNIQUE"],
            "exerciseIds": [], "techniqueId": None,
        }})
        self.assertEqual(response.status_code, 200)
        series = response.json()["data"]["timeAnalysis"]["series"]
        self.assertEqual([item["label"] for item in series], [
            "Média de Força / carga · Supino · Drop set",
            "Soma de Tempo de descanso · Supino · Drop set",
            "Soma de Repetições totais · Supino · Drop set",
            "Soma de Repetições parciais · Supino · Drop set",
            "Média de Repetições parciais / total · Supino · Drop set",
            "Soma de Repetições totais - parciais · Supino · Drop set",
        ])
        self.assertEqual(
            [item["points"][0]["y"] for item in series],
            [85.0, 150.0, 18.0, 6.0, 32.5, 12.0],
        )

    def test_graphql_comparison_has_independent_axis_functions(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, execution_time_seconds=40, rest_time_seconds=60,
        )
        today = timezone.localdate().isoformat()
        response = self._graphql("""
            query($input: ComparisonAnalysisInput!) {
              comparisonAnalysis(input: $input) {
                x { label kind } y { label kind }
                series { label points { x y } }
              }
            }
        """, {"input": {
            "startDate": today, "endDate": today,
            "x": {"field": "SET_POSITION", "function": "RAW"},
            "y": {"field": "WEIGHT", "function": "AVG"},
            "groupBy": ["EXERCISE"], "exerciseIds": [], "techniqueId": None,
        }})
        comparison = response.json()["data"]["comparisonAnalysis"]
        self.assertEqual(comparison["x"]["kind"], "number")
        self.assertEqual(comparison["y"]["label"], "Média de Força / carga")
        self.assertEqual(comparison["series"], [{"label": "Supino", "points": [{"x": 1, "y": 80.0}]}])

    def test_graphql_comparison_accepts_multiple_y_lines(self):
        record = TrainingRecord.objects.create(user=self.user, exercise=self.exercise)
        TrainingSet.objects.create(
            training_record=record, position=1, performed_at=timezone.now(),
            weight_kg=80, execution_time_seconds=40, rest_time_seconds=60,
        )
        TrainingSet.objects.create(
            training_record=record, position=2, performed_at=timezone.now(),
            weight_kg=90, execution_time_seconds=45, rest_time_seconds=75,
        )
        today = timezone.localdate().isoformat()
        response = self._graphql("""
            query($input: ComparisonAnalysisInput!) {
              comparisonAnalysis(input: $input) {
                y { label kind }
                series { label points { x y } }
              }
            }
        """, {"input": {
            "startDate": today, "endDate": today,
            "x": {"field": "SET_POSITION", "function": "RAW"},
            "lines": [
                {"field": "WEIGHT", "function": "RAW"},
                {"field": "REST", "function": "RAW"},
            ],
            "groupBy": ["EXERCISE"], "exerciseIds": [], "techniqueId": None,
        }})
        self.assertEqual(response.status_code, 200)
        comparison = response.json()["data"]["comparisonAnalysis"]
        self.assertEqual(comparison["y"], {"label": "Valores", "kind": "number"})
        self.assertEqual([item["label"] for item in comparison["series"]], [
            "Força / carga · Supino", "Tempo de descanso · Supino",
        ])
        self.assertEqual(
            [[point["y"] for point in item["points"]] for item in comparison["series"]],
            [[80.0, 90.0], [60, 75]],
        )

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
        self.assertRedirects(response, reverse("manager:home"))
        self.assertEqual(User.objects.count(), 1)

    def test_signup_is_blocked_after_first_account(self):
        User.objects.create_user(username="dono", password="senha-segura-123")
        response = self.client.get(reverse("manager:signup"))
        self.assertRedirects(response, reverse("manager:login"))
