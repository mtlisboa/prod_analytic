from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="analytics"),
    path("dados-temporais/", views.time_data, name="analytics_time_data"),
    path("dados-dinamicos/", views.dynamic_data, name="analytics_dynamic_data"),
]
