from django.urls import include, path

from . import views

app_name = "manager"
urlpatterns = [
    path("", include("contexts.manager.features.authentication.urls")),
    path("contextos/", views.home, name="home"),
]
