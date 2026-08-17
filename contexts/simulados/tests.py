from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Intervalo, Meta, MetaMateria, Simulado


class SimuladosFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="matheus", password="senha-segura-123")
        self.other = User.objects.create_user(username="outro", password="senha-segura-123")
        self.client.force_login(self.user)

    def test_context_home_links_academia_and_simulados(self):
        response = self.client.get(reverse("manager:home"))
        self.assertContains(response, "Academia")
        self.assertContains(response, "Simulados")
        self.assertContains(response, reverse("simulados:dashboard"))

    def test_simulation_is_created_with_intervals_and_link(self):
        response = self.client.post(reverse("simulados:create"), {
            "title": "Simulado PF",
            "exam_url": "https://example.com/prova.pdf",
            "exam_date": "2026-08-17",
            "total_questions": 100,
            "correct_answers": 72,
            "wrong_answers": 20,
            "subject": "informatica",
            "total_hours": 2,
            "total_minutes": 30,
            "effective_hours": 2,
            "effective_minutes": 15,
            "rested_hours": 0,
            "rested_minutes": 15,
            "observation": "Prova longa; revisar estatística.",
            "intervals-TOTAL_FORMS": 2,
            "intervals-INITIAL_FORMS": 0,
            "intervals-MIN_NUM_FORMS": 0,
            "intervals-MAX_NUM_FORMS": 1000,
            "intervals-0-position": 1,
            "intervals-0-duration_minutes": 10,
            "intervals-0-note": "Água",
            "intervals-1-position": 2,
            "intervals-1-duration_minutes": 5,
            "intervals-1-note": "Lanche",
        })
        self.assertRedirects(response, reverse("simulados:dashboard"))
        simulation = Simulado.objects.get()
        self.assertEqual(simulation.user, self.user)
        self.assertEqual(simulation.total_time_minutes, 150)
        self.assertEqual(simulation.effective_time_minutes, 135)
        self.assertEqual(simulation.rested_time_minutes, 15)
        self.assertEqual(simulation.subject, "INFORMATICA")
        self.assertEqual(simulation.exam_url, "https://example.com/prova.pdf")
        self.assertEqual(list(Intervalo.objects.values_list("duration_minutes", flat=True)), [10, 5])

    def test_answers_cannot_exceed_total_questions(self):
        response = self.client.post(reverse("simulados:create"), {
            "title": "Inválido", "exam_date": "2026-08-17", "total_questions": 10,
            "correct_answers": 8, "wrong_answers": 5, "subject": "GERAL",
            "total_hours": 1, "total_minutes": 0, "effective_hours": 1, "effective_minutes": 0,
            "rested_hours": 0, "rested_minutes": 0,
            "intervals-TOTAL_FORMS": 0, "intervals-INITIAL_FORMS": 0,
            "intervals-MIN_NUM_FORMS": 0, "intervals-MAX_NUM_FORMS": 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "não pode superar")
        self.assertFalse(Simulado.objects.exists())

    def test_user_only_sees_and_deletes_own_simulations(self):
        own = Simulado.objects.create(user=self.user, title="Meu", exam_date="2026-08-17", subject="GERAL", total_questions=10, correct_answers=8, wrong_answers=2, total_time_minutes=60, effective_time_minutes=50, rested_time_minutes=10)
        private = Simulado.objects.create(user=self.other, title="Privado", exam_date="2026-08-17", subject="GERAL", total_questions=10, correct_answers=9, wrong_answers=1, total_time_minutes=50, effective_time_minutes=50, rested_time_minutes=0)
        response = self.client.get(reverse("simulados:dashboard"))
        self.assertContains(response, "Meu")
        self.assertNotContains(response, "Privado")
        self.assertEqual(self.client.get(reverse("simulados:delete", args=[private.pk])).status_code, 404)
        self.client.post(reverse("simulados:delete", args=[own.pk]))
        self.assertFalse(Simulado.objects.filter(pk=own.pk).exists())

    def test_goal_is_created_with_time_and_subject_targets(self):
        response = self.client.post(reverse("simulados:goal_create"), {
            "exam_name": "Polícia Federal 2027",
            "exam_date": "2027-03-14",
            "exam_hours": 4,
            "exam_minutes": 30,
            "break_hours": 0,
            "break_minutes": 20,
            "observation": "Priorizar conhecimentos específicos.",
            "subjects-TOTAL_FORMS": 2,
            "subjects-INITIAL_FORMS": 0,
            "subjects-MIN_NUM_FORMS": 1,
            "subjects-MAX_NUM_FORMS": 1000,
            "subjects-0-position": 1,
            "subjects-0-subject": "Português",
            "subjects-0-target_accuracy_percent": 85,
            "subjects-1-position": 2,
            "subjects-1-subject": "Informática",
            "subjects-1-target_accuracy_percent": 90,
        })
        self.assertRedirects(response, reverse("simulados:dashboard"))
        goal = Meta.objects.get()
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.exam_time_minutes, 270)
        self.assertEqual(goal.break_time_minutes, 20)
        self.assertEqual(list(MetaMateria.objects.values_list("subject", "target_accuracy_percent")), [("PORTUGUES", 85), ("INFORMATICA", 90)])

    def test_goal_requires_at_least_one_subject_and_valid_accuracy(self):
        response = self.client.post(reverse("simulados:goal_create"), {
            "exam_name": "Prova", "exam_hours": 2, "exam_minutes": 0,
            "break_hours": 0, "break_minutes": 10,
            "subjects-TOTAL_FORMS": 1, "subjects-INITIAL_FORMS": 0,
            "subjects-MIN_NUM_FORMS": 1, "subjects-MAX_NUM_FORMS": 1000,
            "subjects-0-position": 1, "subjects-0-subject": "Matemática",
            "subjects-0-target_accuracy_percent": 120,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certifique-se que este valor seja menor ou igual a 100")
        self.assertFalse(Meta.objects.exists())

    def test_user_cannot_delete_another_users_goal(self):
        goal = Meta.objects.create(user=self.other, exam_name="Privada", exam_time_minutes=180, break_time_minutes=15)
        response = self.client.get(reverse("simulados:goal_delete", args=[goal.pk]))
        self.assertEqual(response.status_code, 404)

    def test_simulation_selects_goal_subject_and_rejects_unknown_subject(self):
        goal = Meta.objects.create(user=self.user, exam_name="PF", exam_time_minutes=240, break_time_minutes=20)
        MetaMateria.objects.create(meta=goal, subject="PORTUGUES", target_accuracy_percent=85, position=1)
        payload = {
            "meta": goal.pk, "subject": "direito", "title": "Bloco 1", "exam_date": "2026-08-17",
            "total_questions": 20, "correct_answers": 15, "wrong_answers": 5,
            "total_hours": 1, "total_minutes": 0, "effective_hours": 1, "effective_minutes": 0,
            "rested_hours": 0, "rested_minutes": 0,
            "intervals-TOTAL_FORMS": 0, "intervals-INITIAL_FORMS": 0,
            "intervals-MIN_NUM_FORMS": 0, "intervals-MAX_NUM_FORMS": 1000,
        }
        response = self.client.post(reverse("simulados:create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selecione uma matéria cadastrada")
        self.assertFalse(Simulado.objects.exists())

    def test_subject_rejects_special_characters(self):
        response = self.client.post(reverse("simulados:create"), {
            "subject": "MATEMÁTICA!", "title": "Bloco", "exam_date": "2026-08-17",
            "total_questions": 10, "correct_answers": 8, "wrong_answers": 2,
            "total_hours": 1, "total_minutes": 0, "effective_hours": 1, "effective_minutes": 0,
            "rested_hours": 0, "rested_minutes": 0,
            "intervals-TOTAL_FORMS": 0, "intervals-INITIAL_FORMS": 0,
            "intervals-MIN_NUM_FORMS": 0, "intervals-MAX_NUM_FORMS": 1000,
        })
        self.assertContains(response, "Use apenas letras sem acentos")
