from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("treinos/historico/", views.training_history, name="training_history"),
]
