from django.urls import path

from . import views

app_name = "simulados"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("novo/", views.create, name="create"),
    path("<int:pk>/excluir/", views.delete, name="delete"),
]
