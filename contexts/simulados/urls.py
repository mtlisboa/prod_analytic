from django.urls import include, path

from . import views

app_name = "simulados"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analises/", include("contexts.simulados.features.analytics.urls")),
    path("novo/", views.create, name="create"),
    path("metas/nova/", views.create_goal, name="goal_create"),
    path("metas/<int:pk>/excluir/", views.delete_goal, name="goal_delete"),
    path("<int:pk>/excluir/", views.delete, name="delete"),
]
