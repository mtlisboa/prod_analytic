import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render
from django.utils import timezone

from contexts.academia.features.training.models import TrainingRecord, TrainingSet

from .forms import AnalyticsFilterForm
from .services import build_analysis


@login_required
def dashboard(request):
    today = timezone.localdate()
    form = AnalyticsFilterForm(request.GET or None, user=request.user)
    if form.is_valid():
        filters = form.cleaned_data
    else:
        filters = {
            "start_date": today.replace(day=1),
            "end_date": today,
            "period": "daily",
            "metric": "sets",
            "technique": None,
        }

    rows, metric = build_analysis(user=request.user, **filters)
    recent_records = TrainingRecord.objects.filter(user=request.user).select_related("exercise").prefetch_related("sets__advanced_technique").annotate(set_total=Count("sets"), avg_weight=Avg("sets__weight_kg"))[:8]
    today_totals = TrainingSet.objects.filter(training_record__user=request.user, performed_at__date=today).aggregate(
        sets=Count("id"), execution=Sum("execution_time_seconds"), rest=Sum("rest_time_seconds")
    )
    total_records = TrainingRecord.objects.filter(user=request.user).count()

    return render(request, "academia/dashboard.html", {
        "filter_form": form,
        "rows": rows,
        "metric": metric,
        "chart_labels": json.dumps([row["label"] for row in rows]),
        "chart_values": json.dumps([row["value"] for row in rows]),
        "recent_records": recent_records,
        "today_totals": today_totals,
        "total_records": total_records,
    })
