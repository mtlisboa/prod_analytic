import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .services import (
    AGGREGATIONS, FIELDS, GROUPS, PERIODS, TIME_METRICS, X_FIELDS, Y_FIELDS,
    build_dynamic_analysis, build_time_analysis, filtered_simulations,
)


def _parse_date(value, fallback):
    try:
        return date.fromisoformat(value) if value else fallback
    except ValueError:
        return None


def _filters(request):
    today = timezone.localdate()
    start_date = _parse_date(request.GET.get("start_date"), today - timedelta(days=90))
    end_date = _parse_date(request.GET.get("end_date"), today)
    if not start_date or not end_date or start_date > end_date:
        raise ValueError("Informe um período válido.")
    meta_id = request.GET.get("meta", "")
    if meta_id and not request.user.metas_simulados.filter(pk=meta_id).exists():
        raise ValueError("A prova visada selecionada é inválida.")
    return {
        "user": request.user,
        "start_date": start_date,
        "end_date": end_date,
        "subject": request.GET.get("subject", ""),
        "meta_id": meta_id,
    }


@login_required
def dashboard(request):
    today = timezone.localdate()
    fields = [
        {"key": key, **definition.__dict__}
        for key, definition in FIELDS.items()
    ]
    config = {
        "timeEndpoint": reverse("simulados:analytics_time_data"),
        "dynamicEndpoint": reverse("simulados:analytics_dynamic_data"),
        "startDate": (today - timedelta(days=90)).isoformat(),
        "endDate": today.isoformat(),
        "fields": fields,
        "timeMetrics": list(TIME_METRICS),
        "xFields": list(X_FIELDS),
        "yFields": list(Y_FIELDS),
        "aggregations": [{"key": key, "label": label} for key, label in AGGREGATIONS.items()],
        "periods": [{"key": key, "label": label} for key, label in PERIODS.items()],
        "groups": [{"key": key, "label": label} for key, label in GROUPS.items()],
    }
    subjects = request.user.simulados.order_by("subject").values_list("subject", flat=True).distinct()
    goals = request.user.metas_simulados.order_by("exam_name")
    return render(request, "simulados/analytics.html", {
        "analysis_config": json.dumps(config), "subjects": subjects, "goals": goals,
    })


@login_required
def time_data(request):
    metrics = request.GET.getlist("metric") or ["accuracy", "effective_time", "rested_time"]
    period = request.GET.get("period", "daily")
    group_by = request.GET.get("group_by", "none")
    if any(metric not in TIME_METRICS for metric in metrics) or period not in PERIODS or group_by not in GROUPS:
        return JsonResponse({"error": "Configuração do gráfico temporal inválida."}, status=400)
    try:
        queryset = filtered_simulations(**_filters(request))
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(build_time_analysis(queryset=queryset, metrics=metrics, period=period, group_by=group_by))


@login_required
def dynamic_data(request):
    x_field = request.GET.get("x", "subject")
    y_field = request.GET.get("y", "accuracy")
    aggregation = request.GET.get("aggregation", "avg")
    group_by = request.GET.get("group_by", "none")
    if x_field not in X_FIELDS or y_field not in Y_FIELDS or aggregation not in AGGREGATIONS or group_by not in GROUPS:
        return JsonResponse({"error": "Configuração do gráfico dinâmico inválida."}, status=400)
    try:
        queryset = filtered_simulations(**_filters(request))
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(build_dynamic_analysis(
        queryset=queryset, x_field=x_field, y_field=y_field,
        aggregation=aggregation, group_by=group_by,
    ))
