from django.urls import path
from . import views

urlpatterns = [
    path("treinos/", views.training_list, name="training_list"),
    path("treinos/novo/", views.create_training, name="training_create"),
    path("treinos/historico/", views.training_history, name="training_history"),
    path("treinos/<int:pk>/editar/", views.update_training, name="training_update"),
    path("treinos/<int:pk>/excluir/", views.delete_training, name="training_delete"),
    path("exercicios/buscar/", views.search_exercises, name="exercise_search"),
]
