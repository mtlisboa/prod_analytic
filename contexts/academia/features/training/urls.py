from django.urls import path
from . import views

urlpatterns = [
    path("treinos/novo/", views.create_training, name="training_create"),
    path("treinos/<int:pk>/editar/", views.update_training, name="training_update"),
    path("treinos/<int:pk>/excluir/", views.delete_training, name="training_delete"),
    path("exercicios/buscar/", views.search_exercises, name="exercise_search"),
]
