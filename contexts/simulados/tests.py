from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Intervalo, Simulado


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
            "hours": 2,
            "minutes": 30,
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
        self.assertEqual(simulation.exam_url, "https://example.com/prova.pdf")
        self.assertEqual(list(Intervalo.objects.values_list("duration_minutes", flat=True)), [10, 5])

    def test_answers_cannot_exceed_total_questions(self):
        response = self.client.post(reverse("simulados:create"), {
            "title": "Inválido", "exam_date": "2026-08-17", "total_questions": 10,
            "correct_answers": 8, "wrong_answers": 5, "hours": 1, "minutes": 0,
            "intervals-TOTAL_FORMS": 0, "intervals-INITIAL_FORMS": 0,
            "intervals-MIN_NUM_FORMS": 0, "intervals-MAX_NUM_FORMS": 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "não pode superar")
        self.assertFalse(Simulado.objects.exists())

    def test_user_only_sees_and_deletes_own_simulations(self):
        own = Simulado.objects.create(user=self.user, title="Meu", exam_date="2026-08-17", total_questions=10, correct_answers=8, wrong_answers=2, total_time_minutes=60)
        private = Simulado.objects.create(user=self.other, title="Privado", exam_date="2026-08-17", total_questions=10, correct_answers=9, wrong_answers=1, total_time_minutes=50)
        response = self.client.get(reverse("simulados:dashboard"))
        self.assertContains(response, "Meu")
        self.assertNotContains(response, "Privado")
        self.assertEqual(self.client.get(reverse("simulados:delete", args=[private.pk])).status_code, 404)
        self.client.post(reverse("simulados:delete", args=[own.pk]))
        self.assertFalse(Simulado.objects.filter(pk=own.pk).exists())
