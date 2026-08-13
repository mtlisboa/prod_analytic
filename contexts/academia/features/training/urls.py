from django.urls import path
from . import views

urlpatterns = [path("treinos/novo/", views.create_training, name="training_create")]
