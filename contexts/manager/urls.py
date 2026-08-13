from django.urls import include, path

app_name = "manager"
urlpatterns = [path("", include("contexts.manager.features.authentication.urls"))]
