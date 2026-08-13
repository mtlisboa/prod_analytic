from django.urls import path
from . import views

urlpatterns = [
    path("exercicios/novo/", views.create_exercise, name="exercise_create"),
    path("tecnicas/nova/", views.create_technique, name="technique_create"),
]
