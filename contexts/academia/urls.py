from django.urls import include, path

app_name = "academia"
urlpatterns = [
    path("", include("contexts.academia.features.analytics.urls")),
    path("", include("contexts.academia.features.catalog.urls")),
    path("", include("contexts.academia.features.training.urls")),
]
