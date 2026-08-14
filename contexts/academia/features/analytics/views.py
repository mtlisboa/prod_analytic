import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render
from django.utils import timezone

from contexts.academia.features.training.models import TrainingRecord, TrainingSet

from .forms import AnalyticsFilterForm
from .services import AXES, METRICS, build_comparison, build_time_analysis


@login_required
def dashboard(request):
    today = timezone.localdate()
    query = request.GET.copy()
    if query and "metrics" not in query and query.get("metric"):
        query.setlist("metrics", [query["metric"]])
    legacy_axis_map = {
        "sets": "set_position", "weight_per_set": "weight",
        "rest_time": "rest", "rest_per_set": "rest",
        "execution_per_set": "execution",
    }
    if query and "x_axis" not in query and query.get("x_metric"):
        query["x_axis"] = legacy_axis_map.get(query["x_metric"], "set_position")
    if query and "y_axis" not in query and query.get("y_metric"):
        query["y_axis"] = legacy_axis_map.get(query["y_metric"], "weight")
    form = AnalyticsFilterForm(query or None, user=request.user)
    if form.is_valid():
        filters = form.cleaned_data
    else:
        filters = {
            "start_date": today.replace(day=1),
            "end_date": today,
            "period": "daily",
            "metrics": list(METRICS),
            "exercises": list(request.user.exercises.filter(active=True)),
            "x_axis": "set_position",
            "y_axis": "weight",
            "group_by": "exercise",
            "technique": None,
        }

    analysis_filters = {
        key: filters[key]
        for key in ("start_date", "end_date", "period", "technique")
    }
    chart_labels, chart_series = build_time_analysis(
        user=request.user, metrics=filters["metrics"], exercises=filters["exercises"],
        **analysis_filters,
    )
    comparison = build_comparison(
        user=request.user, start_date=filters["start_date"], end_date=filters["end_date"],
        x_axis=filters["x_axis"], y_axis=filters["y_axis"],
        technique=filters["technique"], exercises=filters["exercises"],
        group_by=filters["group_by"],
    )
    rows = [
        {
            "label": label,
            "values": [item["values"][index] for item in chart_series],
        }
        for index, label in enumerate(chart_labels)
    ]
    recent_records = TrainingRecord.objects.filter(user=request.user).select_related("exercise").prefetch_related("sets__advanced_technique").annotate(set_total=Count("sets"), avg_weight=Avg("sets__weight_kg"))[:8]
    today_totals = TrainingSet.objects.filter(training_record__user=request.user, performed_at__date=today).aggregate(
        sets=Count("id"), execution=Sum("execution_time_seconds"), rest=Sum("rest_time_seconds")
    )
    total_records = TrainingRecord.objects.filter(user=request.user).count()

    return render(request, "academia/dashboard.html", {
        "filter_form": form,
        "rows": rows,
        "chart_series": chart_series,
        "chart_data": json.dumps({"labels": chart_labels, "series": chart_series}),
        "relation_data": json.dumps(comparison),
        "comparison": comparison,
        "x_axis": AXES[filters["x_axis"]],
        "y_axis": AXES[filters["y_axis"]],
        "recent_records": recent_records,
        "today_totals": today_totals,
        "total_records": total_records,
    })
