from django.urls import path
from . import views

urlpatterns = [
    path("exercicios/", views.exercise_list, name="exercise_list"),
    path("exercicios/novo/", views.create_exercise, name="exercise_create"),
    path("exercicios/<int:pk>/editar/", views.update_exercise, name="exercise_update"),
    path("exercicios/<int:pk>/excluir/", views.delete_exercise, name="exercise_delete"),
    path("tecnicas/", views.technique_list, name="technique_list"),
    path("tecnicas/nova/", views.create_technique, name="technique_create"),
    path("tecnicas/<int:pk>/editar/", views.update_technique, name="technique_update"),
    path("tecnicas/<int:pk>/excluir/", views.delete_technique, name="technique_delete"),
]
