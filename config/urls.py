from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/analytics/graphql/", include("contexts.academia.features.analytics_graphql.urls")),
    path("", include("contexts.manager.urls")),
    path("academia/", include("contexts.academia.urls")),
    path("simulados/", include("contexts.simulados.urls")),
]
